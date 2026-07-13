"""Load the Form 2553 spec — Election by a Small Business Corporation (Rev. December 2017).
WO-26, SPINE S-20b. Greenfield (gap-checked 404 at WO-22 2026-07-06 and re-confirmed 2026-07-12).

═══════════════════════════════════════════════════════════════════════════
WHAT THIS IS
═══════════════════════════════════════════════════════════════════════════
Form 2553 is the §1362(a) S-corporation ELECTION — a structural election, not a tax computation.
A corporation (or an entity eligible to elect to be treated as a corporation) that meets the eight
Who May Elect tests files it no more than 2 months and 15 days after the beginning of the effective
tax year (or any time during the preceding year). A timely-electing eligible entity is DEEMED
classified as a corporation — no Form 8832 (the WO-22 boundary in reverse). Late elections ride
Rev. Proc. 2013-30 (or a §1362(b)(5) PLR). Print-first: paper/fax only, no MeF channel.

v1 SCOPE — PROPOSED (Gate-1 walk W1-W4 AWAITING KEN; see f2553_source_brief.md):
W1. Eligibility diagnostics (the 8 tests): shareholder count with spouse/family aggregation (item G),
    ineligible-shareholder/NRA screens, ineligible-corporation screen, one-class-of-stock preparer-
    asserted, the §1.1362-5 five-year re-election bar.
W2. The election-window calculator (§1362(b)): deadline = day-before-corresponding-day of the second
    following month + 15 days (no corresponding day -> last day of that month); preceding-year filings
    timely; pre-first-day elections invalid without a prior year. The THREE published i2553 examples
    (Jan 7 -> Mar 21 · Jan 1 -> Mar 15 · Nov 8 -> Jan 22) are pinned scenarios.
W3. Late relief (Rev. Proc. 2013-30): corporate path reqs 1-5 / the 6a-c alternative (lifts the
    3yr75d cap) / entity path + Part IV representations; the page-1 margin legend; the §1362(b)(5)
    PLR fallback ($14,500, Rev. Proc. 2026-1 App. A (A)(3)(c)(i)); Rev. Proc. 2022-19 §3.03 for
    consent/signature defects.
W4. Consents + Part II + print scope: required-consent timing (filed before vs on/after item E);
    who-signs rules (community property BOTH spouses; ESBT trustee+deemed owner; QSST deemed owner);
    F(2)/(4) forces Part II O+(P|Q|R); Q1 user fee $5,750 (YEAR-KEYED — Rev. Proc. 2026-1, supersedes
    the printed $6,200); QSST Part III per-trust (transfer-date gate); entity_types ['1120S'].

CARRIED [UNVERIFIED]: none — verbatim vs current FINAL Form 2553 Rev. 12-2017 + i2553 Rev. 12-2020 +
Rev. Proc. 2026-1 App. A (fee verified in IRB 2026-1 PDF). Filing addresses live-verified vs the
irs.gov where-to-file page (reviewed 2026-03-30) — the printed 12-2020 table is still current.
Re-verify each season: the form revision (reissues irregularly), the Q1 user fee (annual Rev. Proc.),
and the addresses.

SAFETY GUARD — READY_TO_SEED stays False until Ken approves the Gate-1 walk (W1-W4).
FLIPPED 2026-07-12 — Ken APPROVED (live Gate-1 walk, s68 conversation: "Approve" on the plain-English
W1-W4 summary): W1 the eight eligibility tests as diagnostics; W2 the §1362(b) window calculator
(published examples pinned); W3 the Rev. Proc. 2013-30 relief chooser + margin legend + PLR fallback;
W4 consents + Part II ($5,750 fee year-keyed) + QSST gate + entity_types ['1120S'] print-first.
Validated (scratchpad/validate_2553.py, 82/0).
"""
import calendar
from datetime import date, timedelta

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
FORM_ENTITY_TYPES = ["1120S"]  # the election creates the 1120-S filer; print-first, no MeF

# ── Verified constants (f2553_source_brief.md) ──
MAX_SHAREHOLDERS = 100                # §1361(b)(1)(A); i2553 Who May Elect test 2
WINDOW_MONTHS = 2                     # §1362(b) — 2 months ...
WINDOW_EXTRA_DAYS = 15                # ... and 15 days after the tax year begins
LATE_RELIEF_YEARS = 3                 # Rev. Proc. 2013-30 — within 3 years ...
LATE_RELIEF_DAYS = 75                 # ... and 75 days of the item-E effective date
REELECTION_BAR_YEARS = 5              # §1.1362-5 — consent needed before the 5th year after termination
Q1_USER_FEE = 5750                    # Rev. Proc. 2026-1 App. A (A)(3)(a)(ii) — YEAR-KEYED (printed $6,200 superseded)
PLR_1362B5_FEE = 14500                # Rev. Proc. 2026-1 App. A (A)(3)(c)(i) — §1362(b)(5)/§301.9100-3 ruling
MARGIN_LEGEND = "FILED PURSUANT TO REV. PROC. 2013-30"
FILING_ADDRESSES = {                  # live-verified 2026-07-12 (irs.gov where-to-file, reviewed 2026-03-30)
    "eastern": "Department of the Treasury, Internal Revenue Service Center, Kansas City, MO 64999 (fax 855-887-7734)",
    "western": "Department of the Treasury, Internal Revenue Service Center, Ogden, UT 84201 (fax 855-214-7520)",
}


def _election_deadline(effective: date) -> date:
    """§1362(b) / i2553 When To Make the Election: the 2-month period begins on the day of the month
    the tax year begins and ends with the close of the day BEFORE the numerically corresponding day of
    the second calendar month following that month (no corresponding day -> the close of the last day
    of that calendar month); the deadline is 15 days after that.
    Published pins: Jan 7 -> Mar 21 · Jan 1 -> Mar 15 (non-leap) · Nov 8 -> Jan 22."""
    m = effective.month + WINDOW_MONTHS
    y = effective.year + (m - 1) // 12
    m = (m - 1) % 12 + 1
    last_day = calendar.monthrange(y, m)[1]
    if effective.day > last_day:
        period_end = date(y, m, last_day)          # no corresponding day -> last day of the month
    else:
        period_end = date(y, m, effective.day) - timedelta(days=1)
    return period_end + timedelta(days=WINDOW_EXTRA_DAYS)


def _filing_timeliness(effective: date, filed: date, has_prior_tax_year: bool) -> str:
    """Returns 'timely' | 'late' | 'invalid_early'. Timely = filed on/before the 2mo15d deadline and,
    when there is NO prior tax year, not before the first day of the first tax year (i2553 Examples 1/3:
    'an election made before [the first day] won't be valid'). With a prior tax year, any filing during
    the preceding year (approximated as within 12 months before item E) through the deadline is timely."""
    if filed > _election_deadline(effective):
        return "late"
    if filed < effective:
        if not has_prior_tax_year:
            return "invalid_early"
        if filed < effective - timedelta(days=366):
            return "invalid_early"   # earlier than the preceding tax year
    return "timely"


def _shareholder_count_result(raw_count: int, aggregated_count: int) -> tuple:
    """Test 2: spouses (and their estates) count as one; all members of a family (§1361(c)(1)(B)) may
    count as one. Returns (passes, needs_item_g): the test reads the AGGREGATED count; item G is checked
    when the raw J-list exceeds 100 but family aggregation brings it to <= 100."""
    effective = min(int(raw_count), int(aggregated_count))
    passes = effective <= MAX_SHAREHOLDERS
    needs_item_g = int(raw_count) > MAX_SHAREHOLDERS and int(aggregated_count) <= MAX_SHAREHOLDERS
    return (passes, needs_item_g)


def _late_relief_path(is_entity_path, within_3y75d, reasonable_cause, consistent_reporting,
                      six_months_elapsed=False, no_irs_notice=False) -> str:
    """Rev. Proc. 2013-30 path chooser (i2553 Relief for Late Elections). Corporate path = reqs 1-5
    (incl. the 3yr75d clock + consistent-reporting consents). The 6a-c ALTERNATIVE (corporate only)
    lifts the 3yr75d cap when: all reported consistently, >= 6 months since the first S-year return
    was filed, and no IRS problem-notice within 6 months of that filing. Entity path = reqs 1-8 incl.
    the Part IV representations. Anything else -> §1362(b)(5) letter ruling."""
    if not reasonable_cause:
        return "plr_1362b5"
    if is_entity_path:
        return "rp2013_30_entity" if (within_3y75d and consistent_reporting) else "plr_1362b5"
    if within_3y75d and consistent_reporting:
        return "rp2013_30_corp"
    if consistent_reporting and six_months_elapsed and no_irs_notice:
        return "rp2013_30_alt"
    return "plr_1362b5"


def _required_consent_scope(filed_before_effective: bool) -> str:
    """Column J timing rule: filed BEFORE the item-E effective date -> only shareholders who own stock
    on the day the election is made consent; filed ON/AFTER -> everyone who held stock at any time from
    the item-E date through the election date must consent."""
    return "owners_on_election_day" if filed_before_effective else "all_owners_eff_to_file"


def _part_ii_required(tax_year_type: str) -> bool:
    """Item F: checking box (2) fiscal year or box (4) 52-53-week year referenced to a non-December
    month requires Part II (item O plus item P, Q, or R)."""
    return tax_year_type in ("fiscal", "5253_other")


AUTHORITY_TOPICS: list[tuple[str, str]] = [
    ("s_election_2553", "Form 2553 S election (§1362(a)): the 8 Who May Elect tests; the 2mo15d/"
     "preceding-year window; column-K consents; Rev. Proc. 2013-30 late relief; Part II fiscal-year "
     "selection; QSST Part III; deemed §301.7701-3(c)(1)(v) classification (no 8832)."),
]

# Bound as secondary links when present in the target DB (prod has them via irc_sections; a throwaway
# SQLite harness DB does not — links to these skip gracefully there).
EXISTING_SOURCES_TO_REFERENCE: list[str] = ["IRC_1361", "IRC_1362"]

AUTHORITY_SOURCES: list[dict] = [
    {
        "source_code": "IRS_F2553", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Form 2553 (Rev. 12-2017) — Election by a Small Business Corporation",
        "citation": "Form 2553 (Rev. December 2017), Cat. No. 18629R, OMB 1545-0123",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/f2553.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["s_election_2553"],
        "excerpts": [{
            "excerpt_label": "Part I face + note (Rev. 12-2017 verbatim)",
            "excerpt_text": (
                "Note: This election to be an S corporation can be accepted only if all the tests are met "
                "under Who May Elect in the instructions, all shareholders have signed the consent statement, "
                "an officer has signed below, and the exact name and address of the corporation (entity) and "
                "other required form information have been provided. Part I: A Employer identification number; "
                "B Date incorporated; C State of incorporation; D Check the applicable box(es) if the "
                "corporation (entity), after applying for the EIN shown in A above, changed its name or "
                "address; E Election is to be effective for tax year beginning (month, day, year) - Caution: "
                "A corporation (entity) making the election for its first tax year in existence will usually "
                "enter the beginning date of a short tax year that begins on a date other than January 1; "
                "F Selected tax year: (1) Calendar year, (2) Fiscal year ending (month and day), (3) 52-53-week "
                "year ending with reference to the month of December, (4) 52-53-week year ending with reference "
                "to the month of [entry] - If box (2) or (4) is checked, complete Part II; G If more than 100 "
                "shareholders are listed for item J (see page 2), check this box if treating members of a "
                "family as one shareholder results in no more than 100 shareholders; H Name and title of "
                "officer or legal representative whom the IRS may call for more information; I If this S "
                "corporation election is being filed late, I declare I had reasonable cause for not filing "
                "Form 2553 timely..."
            ),
            "summary_text": "Part I items A-I: EIN, date/state incorporated, name/address-change boxes, item E effective date (first-year short-year caution), item F tax year (F2/F4 -> Part II), item G family-aggregation box, item H contact, item I late-election reasonable-cause declaration.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Columns J-N consent grid + Parts II-IV structure (Rev. 12-2017 verbatim substance)",
            "excerpt_text": (
                "Page 2 (Part I continued): J Name and address of each shareholder or former shareholder "
                "required to consent to the election; K Shareholder's Consent Statement - Under penalties of "
                "perjury, I declare that I consent to the election of the above-named corporation (entity) to "
                "be an S corporation under section 1362(a)... I understand my consent is binding and may not "
                "be withdrawn after the corporation (entity) has made a valid election. If seeking relief for "
                "a late filed election, I also declare under penalties of perjury that I have reported my "
                "income on all affected returns consistent with the S corporation election...; L Stock owned "
                "or percentage of ownership (number of shares or percentage, and date(s) acquired); M Social "
                "security number or employer identification number; N Shareholder's tax year ends (month and "
                "day). Part II Selection of Fiscal Tax Year - Note: All corporations using this part must "
                "complete item O and item P, Q, or R. Part III Qualified Subchapter S Trust (QSST) Election "
                "Under Section 1361(d)(2) - Use Part III to make the QSST election only if stock of the "
                "corporation has been transferred to the trust on or before the date on which the corporation "
                "makes its election to be an S corporation. Part IV Late Corporate Classification Election "
                "Representations (five representations, incl. 5a consistent filing or 5b first-year return "
                "not yet due)."
            ),
            "summary_text": "J-N consent grid (K jurat incl. the late-relief income-consistency declaration); Part II = O + (P|Q|R); Part III QSST per-trust with the transfer-date gate; Part IV = the five late-classification representations.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "IRS_I2553", "source_type": "federal_form", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Instructions for Form 2553 (Rev. 12-2020)",
        "citation": "i2553 (Rev. December 2020), Cat. No. 49978N — for use with the December 2017 revision",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/pub/irs-pdf/i2553.pdf",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.5, "topics": ["s_election_2553"],
        "excerpts": [{
            "excerpt_label": "Who May Elect — the eight tests (i2553 12-2020 verbatim substance)",
            "excerpt_text": (
                "A corporation or other entity eligible to elect to be treated as a corporation may elect to "
                "be an S corporation only if it meets all the following tests. 1. It is (a) a domestic "
                "corporation, or (b) a domestic entity eligible to elect to be treated as a corporation, that "
                "timely files Form 2553. 2. It has no more than 100 shareholders. You can treat an individual "
                "and his or her spouse (and their estates) as one shareholder for this test. You can also "
                "treat all members of a family (as defined in section 1361(c)(1)(B)) and their estates as one "
                "shareholder for this test. 3. Its only shareholders are individuals, estates, exempt "
                "organizations described in section 401(a) or 501(c)(3), or certain trusts described in "
                "section 1361(c)(2)(A). 4. It has no nonresident alien shareholders (other than as potential "
                "current beneficiaries of an ESBT). 5. It has only one class of stock (disregarding "
                "differences in voting rights)... all outstanding shares... confer identical rights to "
                "distribution and liquidation proceeds. 6. It isn't one of the following ineligible "
                "corporations: a. a bank or thrift institution that uses the reserve method of accounting for "
                "bad debts under section 585; b. an insurance company subject to tax under subchapter L; "
                "c. a domestic international sales corporation (DISC) or former DISC. 7. It has or will adopt "
                "or change to one of the following tax years: December 31, a natural business year, an "
                "ownership tax year, a section 444 year, a 52-53-week year ending with reference to one of "
                "those, or any other year for which it establishes a business purpose. 8. Each shareholder "
                "consents as explained in the instructions for column K."
            ),
            "summary_text": "The 8 eligibility tests: domestic; <=100 shareholders (spouse + §1361(c)(1)(B) family aggregation); eligible shareholder types only; no NRAs (except ESBT PCBs); one class of stock (voting differences OK); not §585-bank/subch-L-insurer/DISC; a permitted tax year; all consents.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "When To Make the Election + the three published examples (i2553 12-2020 verbatim)",
            "excerpt_text": (
                "Complete and file Form 2553: no more than 2 months and 15 days after the beginning of the "
                "tax year the election is to take effect, or at any time during the tax year preceding the "
                "tax year it is to take effect. For this purpose, the 2-month period begins on the day of the "
                "month the tax year begins and ends with the close of the day before the numerically "
                "corresponding day of the second calendar month following that month. If there is no "
                "corresponding day, use the close of the last day of the calendar month. Example 1. No prior "
                "tax year: a calendar year small business corporation begins its first tax year on January 7. "
                "The 2-month period ends March 6 and 15 days after that is March 21... Because the "
                "corporation had no prior tax year, an election made before January 7 won't be valid. "
                "Example 2. Prior tax year: ... wishes to make an S election for its next tax year beginning "
                "January 1. The 2-month period ends February 28 (29 in leap years) and 15 days after that is "
                "March 15... it can make the election at any time during that prior tax year. Example 3. Tax "
                "year less than 2 1/2 months: ... begins its first tax year on November 8. The 2-month period "
                "ends January 7 and 15 days after that is January 22."
            ),
            "summary_text": "The window: 2mo15d after the effective year begins, or any time in the preceding year. Counting = day before the corresponding day of the 2nd following month, + 15 days (no corresponding day -> last day). Pins: Jan 7 -> Mar 21; Jan 1 -> Mar 15; Nov 8 -> Jan 22; pre-first-day = invalid.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Relief for Late Elections (i2553 12-2020 verbatim substance)",
            "excerpt_text": (
                "When filing Form 2553 for a late S corporation election, the corporation (entity) must enter "
                "in the top margin of the first page of Form 2553 'FILED PURSUANT TO REV. PROC. 2013-30.' "
                "Also, if the late election is made by attaching Form 2553 to Form 1120-S, the corporation "
                "(entity) must enter in the top margin of the first page of Form 1120-S 'INCLUDES LATE "
                "ELECTION(S) FILED PURSUANT TO REV. PROC. 2013-30.' ... Corporate path: (1) intended to be an "
                "S corporation as of the item-E date; (2) fails to qualify solely because Form 2553 wasn't "
                "timely filed; (3) reasonable cause and diligent correction; (4) Form 2553 filed within 3 "
                "years and 75 days of the item-E date; (5) consistent-reporting statements from all "
                "shareholders between the item-E date and filing (column K meets this). A corporation meeting "
                "(1)-(3) but not (4) can still request relief if: (a) the corporation and all shareholders "
                "reported income consistent with S status for all years; (b) at least 6 months have elapsed "
                "since the first S-year return was filed; and (c) neither the corporation nor any shareholder "
                "was notified by the IRS of any problem regarding the S status within 6 months of that "
                "filing. Entity path: the eight requirements including the Part IV representations. To "
                "request relief when these aren't met, generally request a private letter ruling under Rev. "
                "Proc. 2021-1 (or its successor)."
            ),
            "summary_text": "Late relief: page-1 margin legend; corporate reqs 1-5 (3yr75d + column-K consistency); the 6a-c alternative lifts the 3yr75d cap; entity path adds Part IV; else a §1362(b)(5) PLR under the annual Rev. Proc.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Consents, filing, acceptance, end of election (i2553 12-2020 verbatim substance)",
            "excerpt_text": (
                "Column J: For an election filed before the effective date entered for item E, only "
                "shareholders who own stock on the day the election is made need to consent. For an election "
                "filed on or after the effective date, all shareholders or former shareholders who owned "
                "stock at any time during the period beginning on the effective date and ending on the day "
                "the election is made must consent. Column K: if an individual and his or her spouse have a "
                "community interest in the stock or in the income from it, BOTH must consent; each tenant in "
                "common, joint tenant, and tenant by the entirety must consent; a minor's consent is made by "
                "the minor, legal representative, or parent; an estate's by the executor or administrator; an "
                "ESBT's by the trustee and, if a grantor trust, the deemed owner; QSST stock - the deemed "
                "owner consents; other §1361(c)(2) trusts - the §1361(c)(2)(B) person. Where to file "
                "(verified current): Kansas City, MO 64999 (fax 855-887-7734) for CT DE DC GA IL IN KY ME MD "
                "MA MI NH NJ NY NC OH PA RI SC TN VT VA WV WI; Ogden, UT 84201 (fax 855-214-7520) for the "
                "rest. The corporation should generally receive a determination within 60 days (box Q1 adds "
                "about 90 more); follow up at 2 months (5 if Q1) via 800-829-4933. Do not file Form 1120-S "
                "for any tax year before the year the election takes effect. If Form 2553 isn't signed [by an "
                "authorized officer], it won't be considered timely filed. Once made, the election stays in "
                "effect until terminated or revoked; IRS consent generally is required for another election "
                "before the 5th tax year after the first tax year in which the termination or revocation "
                "took effect (Regulations section 1.1362-5)."
            ),
            "summary_text": "Consent timing (before vs on/after item E); who signs (community-property BOTH; ESBT trustee+deemed owner; QSST deemed owner); KC/Ogden addresses + faxes; 60-day determination (+~90 if Q1); no early 1120-S; unsigned = untimely; the §1.1362-5 five-year re-election bar.",
            "is_key_excerpt": True,
        }, {
            "excerpt_label": "Part II — P/Q/R fiscal-year machinery (i2553 12-2020 verbatim substance)",
            "excerpt_text": (
                "Complete Part II if you checked box (2) or (4) in Part I, item F. Item P: automatic approval "
                "under Rev. Proc. 2006-46 - P1 natural business year (section 5.07; attach a statement "
                "showing separately for each month the gross receipts for the most recent 47 months - a "
                "corporation that doesn't have a 47-month period of gross receipts can't automatically "
                "establish a natural business year) or P2 ownership tax year (section 5.08 - shareholders "
                "holding more than half of the shares have the same tax year or are concurrently changing to "
                "it). Item Q: business purpose (prior approval, Rev. Proc. 2002-39) - Q1 request + facts "
                "statement + user fee (the service center forwards to Washington, which bills the fee; do not "
                "pay when filing) + the National Office conference Yes/No; Q2 back-up section 444 election "
                "intent; Q3 agree to adopt/change to a December 31 year if not qualified. Item R: R1 will "
                "make the section 444 election (complete Form 8716 attached or filed separately); R2 agree "
                "to a December 31 year if not qualified. Corporations can't obtain automatic approval under "
                "P1/P2 if under examination, before an appeals office, or before a federal court without "
                "meeting conditions in section 7.03 of Rev. Proc. 2006-46."
            ),
            "summary_text": "Part II routing: F(2)/(4) -> O + (P|Q|R). P1 natural business year needs the 47-month gross-receipts statement; P2 ownership year >50% same-year; Q1 business purpose + user fee + conference box; Q2/Q3 backups; R1 §444 via Form 8716; the under-exam preclusion.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "REVPROC_2013_30", "source_type": "official_guidance", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Rev. Proc. 2013-30 — unified late S-election relief",
        "citation": "Rev. Proc. 2013-30, 2013-36 I.R.B. 173 (3 years 75 days; §4.04 multiple-election supplement)",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/irb/2013-36_IRB",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.0, "topics": ["s_election_2553"],
        "excerpts": [{
            "excerpt_label": "Rev. Proc. 2013-30 unified relief (verbatim substance via i2553)",
            "excerpt_text": (
                "Rev. Proc. 2013-30 provides the exclusive simplified methods for taxpayers to request relief "
                "for late S-corporation elections, ESBT elections, QSST elections, QSub elections, and late "
                "corporate classification elections intended to be effective on the same date as a late "
                "S-corporation election. General requirements: the entity intended to be an S corporation as "
                "of the intended effective date; the election was not timely filed solely because of the "
                "failure to file; reasonable cause and diligent action to correct; requests filed within 3 "
                "years and 75 days of the intended effective date (with the i2553 6a-c exception for "
                "corporations); consistent-reporting statements from all affected shareholders. For "
                "supplemental procedural requirements when seeking relief for multiple late elections, see "
                "section 4.04."
            ),
            "summary_text": "The unified late-election relief vehicle: intended-S + solely-late + reasonable cause + 3yr75d + shareholder consistency; §4.04 stacks multiple late elections (e.g., 8832-equivalent + 2553 via Part IV).",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "REVPROC_2026_1", "source_type": "official_guidance", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Rev. Proc. 2026-1 — letter rulings and user fees (Appendix A)",
        "citation": "Rev. Proc. 2026-1, 2026-1 I.R.B. 1 (Dec. 29, 2025), Appendix A (A)(3)(a) and (A)(3)(c)",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/irb/2026-01_IRB",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.0, "topics": ["s_election_2553"],
        "excerpts": [{
            "excerpt_label": "Appendix A user fees — Part II of Form 2553 + §1362(b)(5) (IRB 2026-1 verbatim)",
            "excerpt_text": (
                "(A)(3)(a) Accounting periods: (i) Form 1128, Application to Adopt, Change, or Retain a Tax "
                "Year... $5,750. (ii) Requests made on Part II of Form 2553, Election by a Small Business "
                "Corporation, to use a fiscal year based on a business purpose (except as provided in "
                "paragraph (A)(4)(a) of this appendix): $5,750. (iii) Letter ruling requests for extensions "
                "of time to file Form 1128, Form 8716, or Part II of Form 2553 under § 301.9100-3: $6,100. "
                "(A)(3)(c)(i) Letter ruling requests for relief under § 301.9100-3, § 1362(b)(5), or "
                "§ 2642(g): $14,500."
            ),
            "summary_text": "Current fees (YEAR-KEYED, re-verify each January): Q1 business-purpose fiscal year = $5,750 (supersedes the $6,200 printed in i2553 12-2020); §1362(b)(5) late-election PLR = $14,500; §301.9100-3 extension rulings = $6,100.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "REVPROC_2006_46", "source_type": "official_guidance", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Rev. Proc. 2006-46 — automatic tax-year adoption/retention/change",
        "citation": "Rev. Proc. 2006-46, 2006-45 I.R.B. 859 (§5.07 natural business year; §5.08 ownership tax year; §4.02/§7.03 preclusions)",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/irb/2006-45_IRB",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.0, "topics": ["s_election_2553"],
        "excerpts": [{
            "excerpt_label": "Item P representations (via the 2553 face, Rev. 12-2017 verbatim)",
            "excerpt_text": (
                "P1 Natural Business Year: I represent that the corporation is adopting, retaining, or "
                "changing to a tax year that qualifies as its natural business year (as defined in section "
                "5.07 of Rev. Proc. 2006-46) and has attached a statement showing separately for each month "
                "the gross receipts for the most recent 47 months... P2 Ownership Tax Year: I represent that "
                "shareholders (as described in section 5.08 of Rev. Proc. 2006-46) holding more than half of "
                "the shares of the stock (as of the first day of the tax year to which the request relates) "
                "of the corporation have the same tax year or are concurrently changing to the tax year that "
                "the corporation adopts, retains, or changes to per item F... I also represent that the "
                "corporation is not precluded by section 4.02 of Rev. Proc. 2006-46 from obtaining automatic "
                "approval of such adoption, retention, or change in tax year."
            ),
            "summary_text": "P1 = §5.07 natural business year + the 47-month gross-receipts statement; P2 = §5.08 ownership tax year (>half the shares); both carry the §4.02 not-precluded representation.",
            "is_key_excerpt": True,
        }],
    },
    {
        "source_code": "REVPROC_2022_19", "source_type": "official_guidance", "source_rank": "primary_official",
        "jurisdiction_code": "US", "title": "Rev. Proc. 2022-19 — taxpayer-assistance procedures for S/QSub defects",
        "citation": "Rev. Proc. 2022-19, 2022-41 I.R.B. 282, §3.03 (cited by Rev. Proc. 2026-1 §6.03(49))",
        "issuer": "Internal Revenue Service", "official_url": "https://www.irs.gov/irb/2022-41_IRB",
        "current_status": "active", "is_substantive_authority": True, "trust_score": 9.0, "topics": ["s_election_2553"],
        "excerpts": [{
            "excerpt_label": "Consent/signature defects — no-PLR paths (IRB 2026-1 §6.03(49) verbatim substance)",
            "excerpt_text": (
                "Except with regard to an inadvertent error relating to a 'permitted year' (as defined in "
                "§ 1378(b) and § 1.1378-1), the absence of a required shareholder consent, or an officer "
                "signature for which there is no other relief as provided in section 3.03 of Rev. Proc. "
                "2022-19, 2022-41 I.R.B. 282, the IRS will not issue a letter ruling under § 1362(f) "
                "addressing whether an inadvertent error or omission, or a missing required consent or "
                "signature (see § 1362(a)(2), § 1.1361-3(a)(2), and § 1.1362-6(a)(1)), on Form 2553 or Form "
                "8869 affects the validity of the S corporation election."
            ),
            "summary_text": "Missing consents/signatures and inadvertent 2553 errors generally ride Rev. Proc. 2022-19 §3.03 assistance procedures, not a PLR (the IRS won't rule under §1362(f) on most such defects).",
            "is_key_excerpt": True,
        }],
    },
]

AUTHORITY_FORM_LINKS: list[tuple[str, str, str]] = [
    ("IRS_F2553", "2553", "governs"), ("IRS_I2553", "2553", "governs"),
    ("REVPROC_2013_30", "2553", "governs"), ("REVPROC_2026_1", "2553", "governs"),
    ("REVPROC_2006_46", "2553", "governs"), ("REVPROC_2022_19", "2553", "governs"),
    ("IRC_1361", "2553", "governs"), ("IRC_1362", "2553", "governs"),
]


F2553_FACTS: list[dict] = [
    {"fact_key": "date_incorporated", "label": "Date incorporated (item B)", "data_type": "date", "required": False, "sort_order": 1},
    {"fact_key": "state_of_incorporation", "label": "State of incorporation (item C)", "data_type": "string", "required": False, "sort_order": 2},
    {"fact_key": "changed_name", "label": "Changed its name after applying for the EIN (item D)", "data_type": "boolean", "required": False, "sort_order": 3},
    {"fact_key": "changed_address", "label": "Changed its address after applying for the EIN (item D)", "data_type": "boolean", "required": False, "sort_order": 4},
    {"fact_key": "election_effective_date", "label": "Election effective for tax year beginning (item E)", "data_type": "date", "required": False, "sort_order": 5,
     "notes": "First year in existence: the EARLIEST of first-had-shareholders / first-had-assets / began-doing-business — usually a short year not beginning Jan 1."},
    {"fact_key": "filing_date", "label": "Date Form 2553 is filed (faxed or mailed)", "data_type": "date", "required": False, "sort_order": 6},
    {"fact_key": "has_prior_tax_year", "label": "Did the entity have a prior tax year? (enables preceding-year filing)", "data_type": "boolean", "required": False, "sort_order": 7},
    {"fact_key": "tax_year_type", "label": "Selected tax year (item F)", "data_type": "choice", "required": False, "sort_order": 8,
     "choices": ["calendar", "fiscal", "5253_dec", "5253_other"], "notes": "fiscal or 5253_other -> Part II required."},
    {"fact_key": "fiscal_year_end", "label": "Fiscal/52-53-week year end (month and day; F(2)/(4))", "data_type": "string", "required": False, "sort_order": 9},
    {"fact_key": "num_shareholders_raw", "label": "Shareholders listed in column J (raw count)", "data_type": "integer", "required": False, "sort_order": 10},
    {"fact_key": "num_shareholders_agg", "label": "Shareholder count after spouse/family aggregation (§1361(c)(1); drives item G)", "data_type": "integer", "required": False, "sort_order": 11},
    {"fact_key": "has_inelig_shareholder", "label": "Any shareholder NOT an individual/estate/§401(a)/§501(c)(3) org/§1361(c)(2)(A) trust? (test 3)", "data_type": "boolean", "required": False, "sort_order": 12},
    {"fact_key": "has_nra_shareholder", "label": "Any nonresident-alien shareholder (other than an ESBT potential current beneficiary)? (test 4)", "data_type": "boolean", "required": False, "sort_order": 13},
    {"fact_key": "one_class_of_stock", "label": "One class of stock (identical distribution/liquidation rights; voting differences OK) — preparer-asserted (test 5)", "data_type": "boolean", "required": False, "sort_order": 14},
    {"fact_key": "ineligible_corp_type", "label": "Ineligible corporation type (test 6)", "data_type": "choice", "required": False, "sort_order": 15,
     "choices": ["none", "bank_585_reserve", "insurance_subch_l", "disc_or_former"]},
    {"fact_key": "is_eligible_entity_filer", "label": "Filer is an eligible entity (LLC etc.) electing to be treated as a corporation (deemed 8832; entity late-relief path)", "data_type": "boolean", "required": False, "sort_order": 16},
    {"fact_key": "officer_signed", "label": "Signed and dated by an authorized officer (unsigned = not timely filed)", "data_type": "boolean", "required": False, "sort_order": 17},
    {"fact_key": "consents_complete", "label": "Every required J row has a signed/dated K consent + L/M/N completed", "data_type": "boolean", "required": False, "sort_order": 18},
    {"fact_key": "has_community_prop_stock", "label": "Any stock (or income from it) held as community property? (BOTH spouses must consent)", "data_type": "boolean", "required": False, "sort_order": 19},
    {"fact_key": "reasonable_cause", "label": "Reasonable cause + diligent correction declared (item I / attached statement)", "data_type": "boolean", "required": False, "sort_order": 20},
    {"fact_key": "consistent_reporting", "label": "All affected shareholders reported income consistent with S status (column K jurat / statements)", "data_type": "boolean", "required": False, "sort_order": 21},
    {"fact_key": "six_months_elapsed", "label": "6+ months elapsed since the first intended-S-year return was filed (alternative req 6b)", "data_type": "boolean", "required": False, "sort_order": 22},
    {"fact_key": "no_irs_notice_6mo", "label": "No IRS problem-notice about S status within 6 months of that filing (alternative req 6c)", "data_type": "boolean", "required": False, "sort_order": 23},
    {"fact_key": "part2_basis", "label": "Part II basis (P1 natural business year / P2 ownership year / Q1 business purpose / R1 §444)", "data_type": "choice", "required": False, "sort_order": 24,
     "choices": ["none", "natural_business", "ownership_year", "business_purpose", "sec_444"]},
    {"fact_key": "has_47mo_receipts", "label": "Has the 47-month gross-receipts history (P1 gate)", "data_type": "boolean", "required": False, "sort_order": 25},
    {"fact_key": "qsst_count", "label": "Number of QSST elections made in Part III (additional copies of page 4)", "data_type": "integer", "required": False, "sort_order": 26},
    {"fact_key": "qsst_xfer_after_elect", "label": "Any QSST stock transfer AFTER the S-election date? (Part III unavailable — separate election)", "data_type": "boolean", "required": False, "sort_order": 27},
    {"fact_key": "prior_term_within_5yr", "label": "S election terminated/revoked within the prior 5 tax years? (§1.1362-5 re-election consent)", "data_type": "boolean", "required": False, "sort_order": 28},
]

F2553_RULES: list[dict] = [
    {"rule_id": "R-2553-ELIG", "title": "Who May Elect — the eight §1361(b) tests", "rule_type": "validation",
     "formula": "eligible iff: domestic corp-or-eligible-entity AND min(num_shareholders_raw, num_shareholders_agg) <= 100 AND not has_inelig_shareholder AND not has_nra_shareholder AND one_class_of_stock AND ineligible_corp_type == none AND permitted tax year AND consents_complete",
     "inputs": ["num_shareholders_raw", "num_shareholders_agg", "has_inelig_shareholder", "has_nra_shareholder",
                "one_class_of_stock", "ineligible_corp_type", "tax_year_type", "consents_complete"],
     "outputs": ["is_eligible_scorp"], "sort_order": 1,
     "description": "W1. The election can be accepted only if ALL eight Who May Elect tests are met: (1) domestic corporation or domestic eligible entity; (2) no more than 100 shareholders — spouses (and their estates) count as one, and all members of a family under §1361(c)(1)(B) may count as one; (3) shareholders are only individuals, estates, §401(a)/§501(c)(3) exempt organizations, or §1361(c)(2)(A) trusts; (4) no nonresident-alien shareholders (other than ESBT potential current beneficiaries); (5) one class of stock (voting-rights differences disregarded); (6) not a §585 reserve-method bank, a subchapter-L insurance company, or a DISC/former DISC; (7) a permitted tax year; (8) every required shareholder consents. One-class-of-stock is preparer-asserted (diagnostic INFO, not adjudicated)."},
    {"rule_id": "R-2553-COUNT", "title": "Shareholder count with spouse/family aggregation (item G)", "rule_type": "calculation",
     "formula": "effective_count = min(num_shareholders_raw, num_shareholders_agg); passes = effective_count <= 100; needs_item_g = num_shareholders_raw > 100 and num_shareholders_agg <= 100",
     "inputs": ["num_shareholders_raw", "num_shareholders_agg"], "outputs": ["count_passes", "needs_item_g"], "sort_order": 2,
     "description": "W1. Test 2 reads the AGGREGATED count: an individual and spouse (and their estates) are one shareholder; all members of a family (§1361(c)(1)(B)) and their estates may be one. Item G is checked when more than 100 are listed in column J but family aggregation brings the count to no more than 100."},
    {"rule_id": "R-2553-WINDOW", "title": "Election window (§1362(b)): 2 months 15 days / preceding year", "rule_type": "calculation",
     "formula": "deadline = (day before the numerically corresponding day of the 2nd calendar month following the month item E begins; no corresponding day -> the last day of that month) + 15 days. timely = filed <= deadline AND (filed >= item E, OR has_prior_tax_year and filed during the preceding tax year). filed before the first day of the FIRST tax year (no prior year) -> invalid_early",
     "inputs": ["election_effective_date", "filing_date", "has_prior_tax_year"], "outputs": ["election_deadline", "timeliness"], "sort_order": 3,
     "description": "W2. File no more than 2 months and 15 days after the beginning of the tax year the election is to take effect, or at any time during the preceding tax year. The 2-month period begins on the day of the month the tax year begins and ends with the close of the day before the numerically corresponding day of the second calendar month following that month (no corresponding day -> the close of the last day of that month). Published pins: first year beginning Jan 7 -> Mar 21; effective Jan 1 with a prior year -> Mar 15 (Feb 28 + 15; 29 in leap years); first year beginning Nov 8 -> Jan 22. An election made before the first day of the first tax year (no prior year) is NOT valid."},
    {"rule_id": "R-2553-LATE", "title": "Late-election relief path (Rev. Proc. 2013-30 / §1362(b)(5) PLR)", "rule_type": "routing",
     "formula": "no reasonable_cause -> plr_1362b5. entity filer: within 3yr75d and consistent -> rp2013_30_entity (Part IV required) else plr_1362b5. corporation: within 3yr75d and consistent -> rp2013_30_corp; else consistent and six_months_elapsed and no_irs_notice_6mo -> rp2013_30_alt; else plr_1362b5",
     "inputs": ["is_eligible_entity_filer", "reasonable_cause", "consistent_reporting", "six_months_elapsed", "no_irs_notice_6mo", "election_effective_date", "filing_date"],
     "outputs": ["late_relief_path"], "sort_order": 4,
     "description": "W3. A late election generally takes effect the FOLLOWING tax year unless relief applies. Rev. Proc. 2013-30 corporate path (reqs 1-5): intended-S as of item E; fails solely for late filing; reasonable cause + diligent correction; filed within 3 years and 75 days of item E; consistent-reporting statements from all item-E-to-filing shareholders (column K satisfies this). The 6a-c ALTERNATIVE lifts the 3yr75d cap (all consistent + 6 months since the first S-year return + no IRS problem-notice within 6 months). The entity path adds the Part IV representations. Every 2013-30 filing carries the page-1 top-margin legend 'FILED PURSUANT TO REV. PROC. 2013-30' (and the 1120-S margin legend when attached). Otherwise: a §1362(b)(5) letter ruling — $14,500 under Rev. Proc. 2026-1 App. A (A)(3)(c)(i). Consent/signature defects may instead ride Rev. Proc. 2022-19 §3.03."},
    {"rule_id": "R-2553-CONSENT", "title": "Required-consent scope and signers (columns J/K)", "rule_type": "validation",
     "formula": "filed before item E -> only shareholders owning stock on the day the election is made consent; filed on/after item E -> all shareholders/former shareholders holding stock at any time from item E through the election date. Community-property stock -> BOTH spouses; ESBT -> trustee + deemed owner (grantor); QSST -> deemed owner; disregarded-LLC-held stock -> the owner",
     "inputs": ["filing_date", "election_effective_date", "consents_complete", "has_community_prop_stock"],
     "outputs": ["required_consent_scope"], "sort_order": 5,
     "description": "W4. The consent set depends on timing: an election filed BEFORE the item-E effective date needs consents only from shareholders who own stock on the day the election is made; filed ON/AFTER item E, everyone who held stock at any time during the item-E-to-election-date period must consent (including former shareholders — column L shows -0- for them). Special signers: community-property spouses BOTH consent (Rev. Proc. 2004-35 for the community-property-only spouse); each tenant in common/joint tenant/tenant by the entirety; minors by self/representative/parent; estates by the executor; ESBTs by the trustee plus the deemed owner of a grantor trust; QSST stock by the deemed owner; other §1361(c)(2) trusts by the §1361(c)(2)(B) person. An unsigned officer signature = not considered timely filed."},
    {"rule_id": "R-2553-PART2", "title": "Part II routing (item F(2)/(4) -> O + P|Q|R)", "rule_type": "routing",
     "formula": "part_ii_required = tax_year_type in (fiscal, 5253_other). If required: item O (new/retaining/changing) AND one of P1 (natural business year — requires the 47-month gross-receipts statement) / P2 (ownership tax year) / Q1 (business purpose + $5,750 user fee + optional Q2/Q3) / R1 (§444 via Form 8716 + optional R2)",
     "inputs": ["tax_year_type", "part2_basis", "has_47mo_receipts"], "outputs": ["part_ii_required"], "sort_order": 6,
     "description": "W4. Checking item F box (2) fiscal year or box (4) 52-53-week year referenced to a non-December month requires Part II: item O plus item P, Q, or R. P1 (Rev. Proc. 2006-46 §5.07 natural business year) requires the attached 47-month monthly gross-receipts statement — without a 47-month history automatic approval is unavailable. P2 = §5.08 ownership tax year (>half the shares same/concurrently-changing year). Q1 = prior-approval business purpose (Rev. Proc. 2002-39) with a user fee ($5,750, Rev. Proc. 2026-1 — YEAR-KEYED; do not pay when filing) and ~90 extra processing days; Q2 = back-up §444 intent; Q3/R2 = agree to a Dec-31 year if not qualified. R1 = §444 election via Form 8716 (attached or separate)."},
    {"rule_id": "R-2553-QSST", "title": "Part III QSST election gate (§1361(d)(2))", "rule_type": "validation",
     "formula": "Part III usable only when corporate stock was transferred to the trust ON OR BEFORE the S-election date; later transfers -> a separate QSST election. Form 2553 cannot be filed with only Part III completed. One Part III (page-4 copy) per QSST; the deemed owner also consents in column K",
     "inputs": ["qsst_count", "qsst_xfer_after_elect"], "outputs": ["qsst_part3_ok"], "sort_order": 7,
     "description": "W4. The income beneficiary (or legal representative) makes the §1361(d)(2) QSST election in Part III only if stock has been transferred to the trust on or before the date the corporation makes its S election; stock transferred after that date requires a separate QSST election filing. Additional QSSTs use additional copies of page 4 (or a separate statement with all Part III information). The deemed owner of the QSST must also consent in column K. Form 2553 can't be filed with only Part III completed."},
    {"rule_id": "R-2553-REELECT", "title": "Five-year re-election bar after termination (§1.1362-5)", "rule_type": "validation",
     "formula": "if an S election terminated or was revoked, IRS consent is generally required for a new election by the corporation (or a successor) for any tax year before the 5th tax year after the first tax year in which the termination/revocation took effect",
     "inputs": ["prior_term_within_5yr"], "outputs": ["needs_irs_consent"], "sort_order": 8,
     "description": "W1. Once made, the election stays in effect until terminated or revoked. After a termination or revocation, IRS consent is generally required for another election on Form 2553 before the 5th tax year after the first tax year in which the termination or revocation took effect (Reg. §1.1362-5)."},
]

F2553_RULE_LINKS: list[tuple[str, str, str, str]] = [
    ("R-2553-ELIG", "IRS_I2553", "primary", "Who May Elect tests 1-8"),
    ("R-2553-ELIG", "IRC_1361", "secondary", "§1361(b) small business corporation"),
    ("R-2553-COUNT", "IRS_I2553", "primary", "Test 2 + item G family aggregation"),
    ("R-2553-COUNT", "IRC_1361", "secondary", "§1361(c)(1) spouse/family one-shareholder"),
    ("R-2553-WINDOW", "IRS_I2553", "primary", "When To Make the Election + Examples 1-3"),
    ("R-2553-WINDOW", "IRC_1362", "secondary", "§1362(b) timing"),
    ("R-2553-LATE", "IRS_I2553", "primary", "Relief for Late Elections (both paths)"),
    ("R-2553-LATE", "REVPROC_2013_30", "primary", "3yr75d + consistency + margin legend"),
    ("R-2553-LATE", "REVPROC_2026_1", "secondary", "$14,500 §1362(b)(5) PLR fee"),
    ("R-2553-LATE", "REVPROC_2022_19", "secondary", "Consent/signature-defect assistance"),
    ("R-2553-CONSENT", "IRS_I2553", "primary", "Columns J/K consent timing + signers"),
    ("R-2553-CONSENT", "IRS_F2553", "secondary", "Column K jurat text"),
    ("R-2553-PART2", "IRS_F2553", "primary", "Part II O/P/Q/R face"),
    ("R-2553-PART2", "REVPROC_2006_46", "primary", "§5.07/§5.08 automatic approval"),
    ("R-2553-PART2", "REVPROC_2026_1", "secondary", "Q1 $5,750 user fee"),
    ("R-2553-QSST", "IRS_F2553", "primary", "Part III face + transfer-date footnote"),
    ("R-2553-QSST", "IRS_I2553", "secondary", "Part III instructions + deemed-owner consent"),
    ("R-2553-REELECT", "IRS_I2553", "primary", "End of Election (§1.1362-5)"),
]

F2553_LINES: list[dict] = [
    # Part I face (print unit)
    {"line_number": "NAME", "description": "Corporation (entity) true name per the charter (+ C/O when shared address)", "line_type": "input", "sort_order": 1},
    {"line_number": "ADDRESS", "description": "Number/street/suite (or P.O. box) + city/state/ZIP", "line_type": "input", "sort_order": 2},
    {"line_number": "A_EIN", "description": "A — Employer identification number ('Applied For' + date if pending)", "line_type": "input", "sort_order": 3},
    {"line_number": "B_DATE_INC", "description": "B — Date incorporated", "line_type": "input", "source_facts": ["date_incorporated"], "sort_order": 4},
    {"line_number": "C_STATE", "description": "C — State of incorporation", "line_type": "input", "source_facts": ["state_of_incorporation"], "sort_order": 5},
    {"line_number": "D_NAME_CHG", "description": "D — Name changed after applying for the EIN (checkbox)", "line_type": "input", "source_facts": ["changed_name"], "sort_order": 6},
    {"line_number": "D_ADDR_CHG", "description": "D — Address changed after applying for the EIN (checkbox)", "line_type": "input", "source_facts": ["changed_address"], "sort_order": 7},
    {"line_number": "E_EFF_DATE", "description": "E — Election effective for tax year beginning (first-year: earliest of shareholders/assets/business)", "line_type": "input", "source_facts": ["election_effective_date"], "sort_order": 8},
    {"line_number": "F1_CAL", "description": "F(1) — Calendar year (checkbox)", "line_type": "input", "source_facts": ["tax_year_type"], "sort_order": 9},
    {"line_number": "F2_FISCAL", "description": "F(2) — Fiscal year ending (month/day) -> Part II required", "line_type": "input", "source_facts": ["tax_year_type", "fiscal_year_end"], "sort_order": 10},
    {"line_number": "F3_5253DEC", "description": "F(3) — 52-53-week year referenced to December (checkbox)", "line_type": "input", "source_facts": ["tax_year_type"], "sort_order": 11},
    {"line_number": "F4_5253OTH", "description": "F(4) — 52-53-week year referenced to another month -> Part II required", "line_type": "input", "source_facts": ["tax_year_type", "fiscal_year_end"], "sort_order": 12},
    {"line_number": "G_FAMAGG", "description": "G — Family-aggregation checkbox (raw J count > 100 but aggregated <= 100)", "line_type": "calculated", "source_rules": ["R-2553-COUNT"], "sort_order": 13},
    {"line_number": "H_OFFICER", "description": "H — Officer/legal representative name and title", "line_type": "input", "sort_order": 14},
    {"line_number": "H_PHONE", "description": "H — Telephone number", "line_type": "input", "sort_order": 15},
    {"line_number": "I_LATE_EXPL", "description": "I — Late-election reasonable-cause explanation (or attached statement)", "line_type": "input", "source_facts": ["reasonable_cause"], "sort_order": 16},
    {"line_number": "SIGN_OFF", "description": "Officer signature + title + date (unsigned = not timely filed)", "line_type": "input", "source_facts": ["officer_signed"], "sort_order": 17},
    # Consent grid (page 2; repeat page for more rows)
    {"line_number": "J_SHAREHOLDER", "description": "J — Shareholder/former-shareholder name + address (disregarded-LLC stock -> the owner)", "line_type": "input", "sort_order": 18},
    {"line_number": "K_CONSENT", "description": "K — Consent statement signature + date per row", "line_type": "input", "source_facts": ["consents_complete"], "sort_order": 19},
    {"line_number": "L_STOCK", "description": "L — Shares or % owned + date(s) acquired (-0- for former shareholders; LLCs use %)", "line_type": "input", "sort_order": 20},
    {"line_number": "M_SSN_EIN", "description": "M — SSN (individuals) or EIN (estate/qualified trust/exempt org)", "line_type": "input", "sort_order": 21},
    {"line_number": "N_TAXYREND", "description": "N — Shareholder tax year end (month/day)", "line_type": "input", "sort_order": 22},
    # Part II
    {"line_number": "O1_NEW", "description": "O1 — New corporation adopting the item-F year", "line_type": "input", "sort_order": 23},
    {"line_number": "O2_RETAIN", "description": "O2 — Existing corporation retaining the item-F year", "line_type": "input", "sort_order": 24},
    {"line_number": "O3_CHANGE", "description": "O3 — Existing corporation changing to the item-F year", "line_type": "input", "sort_order": 25},
    {"line_number": "P1_NBY", "description": "P1 — Natural business year (RP 2006-46 §5.07; attach the 47-month gross-receipts statement)", "line_type": "input", "source_facts": ["part2_basis", "has_47mo_receipts"], "sort_order": 26},
    {"line_number": "P2_OWNERSHIP", "description": "P2 — Ownership tax year (RP 2006-46 §5.08; >half the shares)", "line_type": "input", "source_facts": ["part2_basis"], "sort_order": 27},
    {"line_number": "Q1_BUSPURP", "description": "Q1 — Business-purpose fiscal year (RP 2002-39; user fee — see D_2553_Q1FEE)", "line_type": "input", "source_facts": ["part2_basis"], "sort_order": 28},
    {"line_number": "Q1_CONF", "description": "Q1 — National Office conference if disapproval proposed (Yes/No)", "line_type": "input", "sort_order": 29},
    {"line_number": "Q2_BACKUP444", "description": "Q2 — Back-up §444 election intent", "line_type": "input", "sort_order": 30},
    {"line_number": "Q3_AGREE_CAL", "description": "Q3 — Agree to adopt/change to a Dec-31 year if not qualified", "line_type": "input", "sort_order": 31},
    {"line_number": "R1_SEC444", "description": "R1 — Will make the §444 election (Form 8716 attached or filed separately)", "line_type": "input", "source_facts": ["part2_basis"], "sort_order": 32},
    {"line_number": "R2_AGREE_CAL", "description": "R2 — Agree to a Dec-31 year if ultimately not qualified for §444", "line_type": "input", "sort_order": 33},
    # Part III (per-QSST page-4 copy)
    {"line_number": "P3_BENE", "description": "Part III — Income beneficiary name + address", "line_type": "input", "sort_order": 34},
    {"line_number": "P3_BENE_SSN", "description": "Part III — Income beneficiary SSN", "line_type": "input", "sort_order": 35},
    {"line_number": "P3_TRUST", "description": "Part III — Trust name + address", "line_type": "input", "sort_order": 36},
    {"line_number": "P3_TRUST_EIN", "description": "Part III — Trust EIN", "line_type": "input", "sort_order": 37},
    {"line_number": "P3_XFER_DATE", "description": "Part III — Date stock transferred to the trust (must be on/before the S-election date)", "line_type": "input", "source_rules": ["R-2553-QSST"], "sort_order": 38},
    {"line_number": "P3_SIGN", "description": "Part III — Beneficiary/representative signature + date", "line_type": "input", "sort_order": 39},
    # Part IV (entity late-relief representations — print checklist)
    {"line_number": "P4_REPS", "description": "Part IV — the five late-classification representations (1-4, 5a/5b); auto-included on the entity late path", "line_type": "informational", "source_rules": ["R-2553-LATE"], "sort_order": 40},
    # Computed
    {"line_number": "CALC_DEADLINE", "description": "Computed §1362(b) election deadline (2mo15d corresponding-day math)", "line_type": "calculated", "source_rules": ["R-2553-WINDOW"], "sort_order": 41},
    {"line_number": "CALC_TIMELY", "description": "Computed timeliness (timely / late / invalid_early)", "line_type": "calculated", "source_rules": ["R-2553-WINDOW"], "sort_order": 42},
    {"line_number": "CALC_RELIEF", "description": "Computed late-relief path (rp2013_30_corp / _alt / _entity / plr_1362b5)", "line_type": "calculated", "source_rules": ["R-2553-LATE"], "sort_order": 43},
    {"line_number": "CALC_CONSENT", "description": "Computed required-consent scope (owners on election day vs all owners item E -> filing)", "line_type": "calculated", "source_rules": ["R-2553-CONSENT"], "sort_order": 44},
    {"line_number": "MARGIN_LEGEND", "description": "Page-1 top margin: 'FILED PURSUANT TO REV. PROC. 2013-30' on every 2013-30 relief filing", "line_type": "informational", "source_rules": ["R-2553-LATE"], "sort_order": 45},
]

F2553_DIAGNOSTICS: list[dict] = [
    {"diagnostic_id": "D_2553_INELSH", "title": "Ineligible shareholder type", "severity": "error",
     "condition": "has_inelig_shareholder",
     "message": "An S corporation's only shareholders may be individuals, estates, exempt organizations described in §401(a) or §501(c)(3), or certain trusts described in §1361(c)(2)(A) (including QSSTs and ESBTs with timely elections). A partnership, corporation, IRA (with narrow bank exceptions), or other entity shareholder makes the corporation ineligible (Who May Elect test 3).", "notes": "W1."},
    {"diagnostic_id": "D_2553_NRA", "title": "Nonresident-alien shareholder", "severity": "error",
     "condition": "has_nra_shareholder",
     "message": "The corporation may not have a nonresident-alien shareholder (other than as a potential current beneficiary of an ESBT). A resident-alien shareholder is permitted; a nonresident alien is not (Who May Elect test 4).", "notes": "W1."},
    {"diagnostic_id": "D_2553_100SH", "title": "More than 100 shareholders after aggregation", "severity": "error",
     "condition": "min(num_shareholders_raw, num_shareholders_agg) > 100",
     "message": "The corporation has more than 100 shareholders even after treating each married couple (and their estates) and each §1361(c)(1)(B) family (and their estates) as one shareholder. The election cannot be accepted (Who May Elect test 2).", "notes": "W1."},
    {"diagnostic_id": "D_2553_FAMAGG", "title": "Check item G — family aggregation brings the count to 100 or fewer", "severity": "info",
     "condition": "num_shareholders_raw > 100 and num_shareholders_agg <= 100",
     "message": "More than 100 shareholders are listed for item J, but treating members of a family as one shareholder results in no more than 100. Check the item G box (Who May Elect test 2; §1361(c)(1)(B)).", "notes": "W1."},
    {"diagnostic_id": "D_2553_CLASS1", "title": "One class of stock — preparer-asserted", "severity": "info",
     "condition": "not one_class_of_stock",
     "message": "Confirm the corporation has only one class of stock: all outstanding shares confer identical rights to distribution and liquidation proceeds (differences in voting rights are disregarded, Reg. §1.1361-1(l)). This test is asserted by the preparer, not adjudicated by the software.", "notes": "W1."},
    {"diagnostic_id": "D_2553_INELCORP", "title": "Ineligible corporation", "severity": "error",
     "condition": "ineligible_corp_type != none",
     "message": "The corporation is an ineligible corporation and cannot elect S status: a bank or thrift using the §585 reserve method of accounting for bad debts, an insurance company subject to tax under subchapter L, or a DISC/former DISC (Who May Elect test 6).", "notes": "W1."},
    {"diagnostic_id": "D_2553_EARLY", "title": "Election made before the first day of the first tax year", "severity": "error",
     "condition": "timeliness == invalid_early",
     "message": "Because the corporation (entity) had no prior tax year, an election made before the first day of its first tax year (item E) is not valid. File on or after the item-E date and no later than 2 months and 15 days after it (i2553 Examples 1 and 3).", "notes": "W2."},
    {"diagnostic_id": "D_2553_LATE", "title": "Filed after the §1362(b) deadline — late-election relief needed", "severity": "warning",
     "condition": "timeliness == late",
     "message": "Form 2553 is filed more than 2 months and 15 days after the beginning of the intended effective year (and not during the preceding year). Without relief, the election takes effect the FOLLOWING tax year. Rev. Proc. 2013-30 relief requires: intended-S as of item E, failure solely from late filing, reasonable cause + diligent correction (item I), filing within 3 years and 75 days of item E, and consistent-reporting shareholder statements (column K). Enter 'FILED PURSUANT TO REV. PROC. 2013-30' in the top margin of page 1 (and the corresponding legend on a late-attached 1120-S).", "notes": "W3."},
    {"diagnostic_id": "D_2553_PLR", "title": "Relief requirements unmet — §1362(b)(5) letter ruling", "severity": "warning",
     "condition": "late_relief_path == plr_1362b5",
     "message": "The Rev. Proc. 2013-30 requirements are not met (no reasonable cause, inconsistent reporting, or outside the 3-year-75-day window without the corporate 6a-c alternative). Relief generally requires a §1362(b)(5) private letter ruling — user fee $14,500 under Rev. Proc. 2026-1 Appendix A (A)(3)(c)(i) (year-keyed). For a missing consent or signature defect, Rev. Proc. 2022-19 §3.03 assistance procedures may apply instead of a ruling.", "notes": "W3. Fee re-verify each January."},
    {"diagnostic_id": "D_2553_SIGN", "title": "Officer signature missing", "severity": "error",
     "condition": "not officer_signed",
     "message": "Form 2553 must be signed and dated by the president, vice president, treasurer, assistant treasurer, chief accounting officer, or another authorized corporate officer. If Form 2553 isn't signed, it won't be considered timely filed.", "notes": "W4."},
    {"diagnostic_id": "D_2553_CONSENT", "title": "Shareholder consent grid incomplete", "severity": "error",
     "condition": "not consents_complete",
     "message": "Every required shareholder (column J) must have a signed and dated consent (column K, or a separate attached consent statement carrying the corporation's name/address/EIN and the J-N information), plus columns L (shares/% + dates acquired; -0- for former shareholders), M (SSN/EIN), and N (tax year end). An election filed on or after the item-E effective date also needs consents from FORMER shareholders who held stock between item E and the filing date. The election cannot be accepted without all consents.", "notes": "W4."},
    {"diagnostic_id": "D_2553_CPSPOUSE", "title": "Community-property stock — both spouses must consent", "severity": "warning",
     "condition": "has_community_prop_stock",
     "message": "If an individual and his or her spouse have a community interest in the stock or in the income from it, BOTH must consent in column K (Pub. 555; Rev. Proc. 2004-35 provides relief for a missing community-property-spouse consent). A missing spousal consent is a common cause of invalid elections.", "notes": "W4."},
    {"diagnostic_id": "D_2553_PART2", "title": "Fiscal/52-53-week year selected — Part II required", "severity": "error",
     "condition": "tax_year_type in (fiscal, 5253_other) and part2_basis == none",
     "message": "Item F box (2) or (4) is checked, so Part II must be completed: item O (new/retaining/changing) plus item P (natural business year or ownership tax year, Rev. Proc. 2006-46), item Q (business purpose, Rev. Proc. 2002-39), or item R (§444 election via Form 8716). A fiscal year without a Part II basis cannot be approved.", "notes": "W4."},
    {"diagnostic_id": "D_2553_P1_47MO", "title": "Natural business year needs the 47-month receipts statement", "severity": "error",
     "condition": "part2_basis == natural_business and not has_47mo_receipts",
     "message": "Box P1 requires an attached statement showing, separately for each month, the gross receipts for the most recent 47 months (Rev. Proc. 2006-46 §5.07). A corporation without a 47-month gross-receipts history cannot automatically establish a natural business year — use item Q or R instead.", "notes": "W4."},
    {"diagnostic_id": "D_2553_Q1FEE", "title": "Box Q1 — user fee and extra processing time", "severity": "warning",
     "condition": "part2_basis == business_purpose",
     "message": "A box Q1 business-purpose fiscal-year request carries a user fee — currently $5,750 (Rev. Proc. 2026-1 Appendix A (A)(3)(a)(ii); the $6,200 printed in the 12-2020 instructions is superseded; YEAR-KEYED, re-verify each January). Do NOT pay when filing — the IRS bills it. Expect roughly 90 additional days for acceptance (follow up at 5 months instead of 2), and answer the National Office conference Yes/No box.", "notes": "W4. Fee re-verify each January."},
    {"diagnostic_id": "D_2553_QSST", "title": "QSST transfer after the S-election date — Part III unavailable", "severity": "warning",
     "condition": "qsst_xfer_after_elect",
     "message": "Part III may be used for the §1361(d)(2) QSST election only if the corporation's stock was transferred to the trust ON OR BEFORE the date the corporation makes its S election. Stock transferred afterward requires a separate QSST election filing. Also: Form 2553 cannot be filed with only Part III completed, and the QSST's deemed owner must also consent in column K.", "notes": "W4."},
    {"diagnostic_id": "D_2553_REELECT", "title": "Prior S termination within 5 years — IRS consent needed", "severity": "warning",
     "condition": "prior_term_within_5yr",
     "message": "After an S election terminates or is revoked, IRS consent is generally required for the corporation (or a successor) to re-elect before the 5th tax year after the first tax year in which the termination or revocation took effect (Reg. §1.1362-5).", "notes": "W1."},
    {"diagnostic_id": "D_2553_NO8832", "title": "Eligible entity electing S — no Form 8832 needed", "severity": "info",
     "condition": "is_eligible_entity_filer",
     "message": "An eligible entity (e.g., an LLC) that timely files Form 2553 and meets the S tests is DEEMED to have elected classification as an association taxable as a corporation as of the S election's effective date (Reg. §301.7701-3(c)(1)(v)) — it does not also file Form 8832. (The mirror of the Form 8832 spec's D_8832_2553.)", "notes": "W4."},
    {"diagnostic_id": "D_2553_FOLLOWUP", "title": "Filing, acceptance follow-up, and the no-early-1120-S rule", "severity": "info",
     "condition": "always (informational on print)",
     "message": "Mail the ORIGINAL (no photocopies) or fax: Kansas City, MO 64999 / fax 855-887-7734 (CT DE DC GA IL IN KY ME MD MA MI NH NJ NY NC OH PA RI SC TN VT VA WV WI) or Ogden, UT 84201 / fax 855-214-7520 (all other states) — verified current 2026. Expect a determination within 60 days (about 90 more if Q1); follow up at 2 months (5 if Q1) at 800-829-4933. Keep proof of filing (certified/registered receipt, stamped copy, or IRS acceptance letter). Do NOT file Form 1120-S for any tax year before the election takes effect — keep filing Form 1120 (or the prior return) until it does. Certain late elections may instead be attached to the first/current Form 1120-S.", "notes": "W4. Addresses year-watched."},
]

F2553_SCENARIOS: list[dict] = [
    {"scenario_name": "2553-A — Example 2 pin: prior year, effective Jan 1 -> deadline Mar 15", "scenario_type": "normal", "sort_order": 1,
     "inputs": {"election_effective_date": "2026-01-01", "filing_date": "2026-03-15", "has_prior_tax_year": True},
     "expected_outputs": {"election_deadline": "2026-03-15", "timeliness": "timely"},
     "notes": "i2553 Example 2 verbatim: the 2-month period ends February 28 (29 in leap years) and 15 days after that is March 15; a prior-year filer can also file any time during the preceding year."},
    {"scenario_name": "2553-B — Example 1 pin: first year begins Jan 7 -> deadline Mar 21", "scenario_type": "normal", "sort_order": 2,
     "inputs": {"election_effective_date": "2026-01-07", "filing_date": "2026-03-21", "has_prior_tax_year": False},
     "expected_outputs": {"election_deadline": "2026-03-21", "timeliness": "timely"},
     "notes": "i2553 Example 1 verbatim: the 2-month period ends March 6 and 15 days after that is March 21."},
    {"scenario_name": "2553-C — Example 3 pin: first year begins Nov 8 -> deadline Jan 22", "scenario_type": "normal", "sort_order": 3,
     "inputs": {"election_effective_date": "2025-11-08", "filing_date": "2026-01-22", "has_prior_tax_year": False},
     "expected_outputs": {"election_deadline": "2026-01-22", "timeliness": "timely"},
     "notes": "i2553 Example 3 verbatim (tax year less than 2 1/2 months): the 2-month period ends January 7 and 15 days after that is January 22."},
    {"scenario_name": "2553-D — no corresponding day: begins Dec 31 -> deadline Mar 15", "scenario_type": "edge", "sort_order": 4,
     "inputs": {"election_effective_date": "2025-12-31", "filing_date": "2026-03-15", "has_prior_tax_year": False},
     "expected_outputs": {"election_deadline": "2026-03-15", "timeliness": "timely"},
     "notes": "There is no February 31, so the 2-month period ends with the close of the last day of February (Feb 28, 2026) and the deadline is 15 days later: March 15 (the counting rule's no-corresponding-day branch)."},
    {"scenario_name": "2553-E — pre-first-day election is invalid (no prior year)", "scenario_type": "failure", "sort_order": 5,
     "inputs": {"election_effective_date": "2026-01-07", "filing_date": "2026-01-02", "has_prior_tax_year": False},
     "expected_outputs": {"timeliness": "invalid_early", "diagnostic": "D_2553_EARLY"},
     "notes": "i2553 Example 1's caution: because the corporation had no prior tax year, an election made before January 7 won't be valid."},
    {"scenario_name": "2553-F — family aggregation: 105 raw / 98 aggregated -> item G", "scenario_type": "edge", "sort_order": 6,
     "inputs": {"num_shareholders_raw": 105, "num_shareholders_agg": 98},
     "expected_outputs": {"count_passes": True, "needs_item_g": True, "diagnostic": "D_2553_FAMAGG"},
     "notes": "Who May Elect test 2 + item G: more than 100 listed in column J, but §1361(c)(1)(B) family aggregation brings the count to <= 100 -> check box G; the election can be accepted."},
    {"scenario_name": "2553-G — 103 shareholders even after aggregation -> ineligible", "scenario_type": "failure", "sort_order": 7,
     "inputs": {"num_shareholders_raw": 110, "num_shareholders_agg": 103},
     "expected_outputs": {"count_passes": False, "diagnostic": "D_2553_100SH"},
     "notes": "The aggregated count still exceeds 100 -> test 2 fails; the election cannot be accepted."},
    {"scenario_name": "2553-H — late corporate path within 3yr75d (Rev. Proc. 2013-30)", "scenario_type": "edge", "sort_order": 8,
     "inputs": {"election_effective_date": "2026-01-01", "filing_date": "2026-09-01", "has_prior_tax_year": True,
                "is_eligible_entity_filer": False, "reasonable_cause": True, "consistent_reporting": True},
     "expected_outputs": {"timeliness": "late", "late_relief_path": "rp2013_30_corp", "margin_legend": "FILED PURSUANT TO REV. PROC. 2013-30", "diagnostic": "D_2553_LATE"},
     "notes": "Filed Sep 1 for a Jan 1 effective date (deadline Mar 15) -> late; reasonable cause + consistency + within 3 years 75 days -> the Rev. Proc. 2013-30 corporate path with the page-1 margin legend."},
    {"scenario_name": "2553-I — beyond 3yr75d: the 6a-c alternative vs the PLR", "scenario_type": "edge", "sort_order": 9,
     "inputs": {"is_eligible_entity_filer": False, "reasonable_cause": True, "consistent_reporting": True,
                "within_3y75d": False, "six_months_elapsed": True, "no_irs_notice_6mo": True},
     "expected_outputs": {"late_relief_path": "rp2013_30_alt"},
     "notes": "Outside the 3-year-75-day window, a CORPORATION can still get 2013-30 relief when all returns were consistent, 6+ months have passed since the first S-year return, and no IRS problem-notice arrived within 6 months (i2553 reqs 6a-c). The same facts WITHOUT 6a-c -> plr_1362b5 ($14,500)."},
    {"scenario_name": "2553-J — fiscal year without the P1 receipts history", "scenario_type": "failure", "sort_order": 10,
     "inputs": {"tax_year_type": "fiscal", "fiscal_year_end": "9/30", "part2_basis": "natural_business", "has_47mo_receipts": False},
     "expected_outputs": {"part_ii_required": True, "diagnostic": "D_2553_P1_47MO"},
     "notes": "F(2) forces Part II; P1 without a 47-month gross-receipts history cannot automatically establish a natural business year (Rev. Proc. 2006-46 §5.07) -> use Q or R instead."},
]

FORMS: list[dict] = [
    {
        "identity": {"form_number": "2553", "form_title": "Form 2553 — Election by a Small Business Corporation (Rev. 12-2017)",
                     "notes": "WO-26 (SPINE S-20b). Structural §1362(a) S-election, print-first (paper/fax only — no MeF). The eight Who May Elect tests (<=100 shareholders w/ spouse + §1361(c)(1)(B) family aggregation -> item G; eligible shareholder types; no NRAs; one class of stock preparer-asserted; not §585-bank/subch-L/DISC; permitted tax year; all consents). The §1362(b) window calculator: 2mo15d corresponding-day math (i2553 Examples 1-3 pinned: Jan 7 -> Mar 21 / Jan 1 -> Mar 15 / Nov 8 -> Jan 22; no-corresponding-day -> last day; pre-first-day invalid; preceding-year filings timely). Late relief Rev. Proc. 2013-30 (corporate 1-5 / 6a-c alternative / entity path + Part IV; page-1 margin legend) else §1362(b)(5) PLR $14,500 (Rev. Proc. 2026-1). Consent timing (before vs on/after item E) + who-signs (community property BOTH; ESBT trustee+deemed owner; QSST deemed owner). Part II: F(2)/(4) -> O + (P1 47-month receipts | P2 ownership | Q1 $5,750 fee YEAR-KEYED | R1 §444/8716). Part III QSST per-trust (transfer-date gate). Deemed §301.7701-3(c)(1)(v) classification (no 8832; pairs with WO-22). Addresses live-verified 2026 (KC/Ogden). Re-verify each season: form revision, Q1 fee, addresses. entity_types ['1120S']."},
        "facts": F2553_FACTS, "rules": F2553_RULES, "rule_links": F2553_RULE_LINKS,
        "lines": F2553_LINES, "diagnostics": F2553_DIAGNOSTICS, "scenarios": F2553_SCENARIOS,
    },
]

# Staged DRAFT deliberately (the new-FAs-default-ACTIVE trap, s6/s65 lessons): the tts build leg
# activates + writes runners + refreshes the export-verbatim mirrors in ONE motion.
FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-2553-WINDOW", "title": "The §1362(b) deadline matches the three published i2553 examples", "assertion_type": "reconciliation",
     "entity_types": ["1120S"], "status": "draft", "sort_order": 1,
     "description": "The 2mo15d corresponding-day computation reproduces i2553 Examples 1-3 exactly (Jan 7 -> Mar 21; Jan 1 -> Mar 15 non-leap; Nov 8 -> Jan 22) and the no-corresponding-day branch (Dec 31 -> Mar 15).",
     "definition": {"rule": "R-2553-WINDOW", "check": "deadline(effective) = (day before corresponding day of month+2, else last day) + 15 days; pins: 01-07->03-21, 01-01->03-15, 11-08->01-22, 12-31->03-15"}},
    {"assertion_id": "FA-2553-COUNT", "title": "Shareholder gate reads the aggregated count; item G when raw > 100 >= aggregated", "assertion_type": "reconciliation",
     "entity_types": ["1120S"], "status": "draft", "sort_order": 2,
     "description": "count_passes = min(raw, aggregated) <= 100; needs_item_g = raw > 100 and aggregated <= 100.",
     "definition": {"rule": "R-2553-COUNT", "check": "min(raw, agg) <= 100; item G iff raw > 100 and agg <= 100"}},
    {"assertion_id": "FA-2553-8832", "title": "A timely S-election is a deemed classification election (no Form 8832)", "assertion_type": "reconciliation",
     "entity_types": ["1120S"], "status": "draft", "sort_order": 3,
     "description": "An eligible entity electing S files ONLY Form 2553 (deemed §301.7701-3(c)(1)(v) association election); the mirror of FA-8832-2553.",
     "definition": {"rule": "R-2553-ELIG", "check": "eligible-entity S election -> Form 2553 only; no 8832 document in the filing set"}},
]


class Command(BaseCommand):
    help = "Load the Form 2553 spec (S-corporation election, Rev. 12-2017). Refuses to seed until READY_TO_SEED=True (Gate-1 W1-W4)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._guard()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLoad Form 2553 spec (Election by a Small Business Corporation)\n"))
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
                "\nREFUSING TO SEED FORM 2553: not cleared.\n\n"
                "Gated until Ken approves the Gate-1 walk (W1 eligibility tests; W2 election-window\n"
                "calculator; W3 Rev. Proc. 2013-30 late relief; W4 consents + Part II + print scope)\n"
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
        # Existing shared sources (IRC 1361/1362 via irc_sections) — bind when present; a throwaway
        # SQLite harness DB won't have them, and their links skip gracefully there.
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
        self.stdout.write("Form 2553 loaded.")
        self.stdout.write(f"  2553: facts {len(F2553_FACTS)} / rules {len(F2553_RULES)} / lines {len(F2553_LINES)} / diag {len(F2553_DIAGNOSTICS)} / tests {len(F2553_SCENARIOS)} / FA {len(FLOW_ASSERTIONS)}")
        self.stdout.write("=" * 60)
