# Source Brief — Form 2553, Election by a Small Business Corporation

**WO-26 · SPINE S-20b · greenfield RS-first (print-first unit; pairs with WO-22 Form 8832, which routes S-elections here)**
Research pass 2026-07-12, verbatim vs current FINAL Form 2553 (Rev. 12-2017) + i2553 (Rev. 12-2020) + Rev. Proc. 2026-1
Appendix A. Nothing [UNVERIFIED]. Filing addresses live-verified vs irs.gov where-to-file (page reviewed 2026-03-30).

---

## Sources

| source_code | title | citation |
|---|---|---|
| `IRS_F2553` | Form 2553 — Election by a Small Business Corporation | Form 2553 (**Rev. December 2017**), Cat. No. 18629R, OMB 1545-0123 (current — no annual reissue; 4 pages) |
| `IRS_I2553` | Instructions for Form 2553 | i2553 (**Rev. December 2020**), Cat. No. 49978N (current; "for use with the December 2017 revision") |
| `IRC_1362` | IRC §1362 — Election; revocation; termination | §1362(a) election · §1362(b) timing · §1362(b)(5) late-relief authority |
| `IRC_1361` | IRC §1361 — S corporation defined | §1361(b) small business corporation tests · §1361(c)(1) family aggregation · §1361(c)(2) eligible trusts · §1361(d) QSST |
| `REVPROC_2013_30` | Rev. Proc. 2013-30 — unified late S-election relief | Rev. Proc. 2013-30, 2013-36 I.R.B. 173 (3-years-75-days; §4.04 multiple-election supplement) |
| `REVPROC_2026_1` | Rev. Proc. 2026-1 — letter rulings + user fees | Rev. Proc. 2026-1, 2026-1 I.R.B. 1 (Appendix A (A)(3)(a): Part II business-purpose fee **$5,750**; (A)(3)(c)(i) §1362(b)(5)/§301.9100-3 ruling **$14,500**) — supersedes the $6,200 printed in i2553 12-2020 |
| `REVPROC_2006_46` | Rev. Proc. 2006-46 — automatic tax-year approval | §5.07 natural business year · §5.08 ownership tax year · §4.02 preclusions (item P) |
| `REVPROC_2022_19` | Rev. Proc. 2022-19 — taxpayer-assistance procedures (S/QSub defects) | 2022-41 I.R.B. 282 §3.03 (consent/signature defects — no-PLR paths; cited by Rev. Proc. 2026-1 §6.03(49)) |

---

## What this is

A corporation **or an entity eligible to elect to be treated as a corporation** files Form 2553 to elect under
**§1362(a)** to be an **S corporation**. An eligible entity that meets the tests and timely files is **deemed** to have
made the entity-classification election — it "doesn't need to file Form 8832" (i2553 Purpose of Form; the WO-22 8832
boundary in reverse). This is a **structural election, not a return computation** — the value in-app is: eligibility
diagnostics, the election-window/late-relief calculator, the shareholder-consent grid (autofillable from the 1120-S
shareholder records), and a correct print unit that can be faxed/mailed or attached to the first 1120-S.

---

## The form face (verbatim map, Rev. 12-2017 — 4 pages)

**Part I — Election Information (p. 1)**
- Header grid: **Name** / street / city-state-ZIP · **A** EIN · **B** date incorporated · **C** state of incorporation.
- **D** checkbox(es): after applying for the EIN in A, the entity changed its **name** or **address**.
- **E** effective date of election (tax year beginning) — with the first-year caution (short-year beginning date).
- **F** selected tax year: **(1)** calendar year · **(2)** fiscal year ending (month/day) · **(3)** 52-53-week year
  referenced to December · **(4)** 52-53-week year referenced to another month. **If (2) or (4) → Part II required.**
- **G** checkbox: if more than 100 shareholders are listed in item J, treating family members as one shareholder
  brings the count to ≤100 (test 2, Who May Elect).
- **H** name/title of officer or legal representative the IRS may call + telephone.
- **I** late-election reasonable-cause declaration (free text; doubles as the Rev. Proc. 2013-30 statement; the
  entity-path filer also declares the Part IV representations are true).
- **Sign Here**: officer signature · title · date (perjury jurat). *Unsigned = not considered timely filed (i2553).*

**Part I continued (p. 2) — the consent grid** (additional copies of page 2 for more rows):
- **J** name and address of each shareholder/former shareholder **required to consent** ·
- **K** Shareholder's Consent Statement — signature + date per row (perjury jurat; includes the late-relief
  income-consistency declaration) ·
- **L** stock owned **or percentage of ownership** (number of shares or %, and date(s) acquired; **-0- for former
  shareholders; LLCs enter percentage**) ·
- **M** SSN (individuals) or EIN (estate/qualified trust/exempt org) ·
- **N** shareholder's tax year ends (month/day).

**Part II — Selection of Fiscal Tax Year (p. 3)** — only if F(2) or F(4); **must complete O and (P, Q, or R)**:
- **O** the corporation is: **O1** new, adopting the item-F year · **O2** existing, retaining it · **O3** existing,
  changing to it.
- **P** Rev. Proc. 2006-46 automatic approval: **P1** natural business year (§5.07; attach the 47-month gross-receipts
  statement) · **P2** ownership tax year (§5.08; >half the shares same/concurrently-changing year). Both carry the
  §4.02 not-precluded representation.
- **Q** business purpose (prior-approval Rev. Proc. 2002-39): **Q1** request + facts statement + **user fee** (+
  Yes/No National-Office conference box) · **Q2** back-up §444 election intent · **Q3** agree to adopt/change to a
  December 31 year if ultimately not qualified.
- **R** §444: **R1** will make the §444 election (**Form 8716** attached or filed separately) · **R2** agree to a
  December 31 year if not qualified.

**Part III — QSST Election under §1361(d)(2) (p. 4)** — per-trust (additional copies of page 4): income beneficiary
name/address + SSN · trust name/address + EIN · date stock transferred to the trust · beneficiary/representative
signature + date. *Use Part III only when stock was transferred to the trust **on or before** the date the corporation
makes the S election; later transfers → separate QSST election. Form 2553 can't be filed with only Part III completed.*

**Part IV — Late Corporate Classification Election Representations (p. 4)** — the five representations (eligible
entity per §301.7701-3(a) · intended corporate classification as of the effective date · fails corporate status solely
for lack of a timely/deemed 8832 · fails S status solely for lack of a timely 2553 · **5a** consistent filing for all
intended-S years **or 5b** first-year return not yet due).

---

## Key rules (verbatim substance — for diagnostics + the window calculator)

- **Who May Elect — all 8 tests (i2553):** (1) domestic corporation or domestic eligible entity; (2) **≤100
  shareholders** — spouse (+estates) count as one; **all members of a family** (§1361(c)(1)(B)) + their estates may
  count as one (item G box when needed); (3) shareholders only individuals, estates, **§401(a)/§501(c)(3) exempt
  orgs**, or **§1361(c)(2)(A) trusts** (QSST §1361(d)(2) · ESBT §1361(e)(3)); (4) **no nonresident-alien
  shareholders** (except as ESBT potential current beneficiaries); (5) **one class of stock** — voting-rights
  differences disregarded; identical distribution/liquidation rights (§1.1361-1(l)); (6) not an ineligible
  corporation: **§585 reserve-method bank/thrift · subchapter-L insurance company · DISC/former DISC**; (7) a
  permitted tax year (Dec-31 / natural business year / ownership year / §444 / 52-53-week on those / business-purpose
  other); (8) every required shareholder consents.
- **When to elect (§1362(b); i2553):** **no more than 2 months and 15 days after the beginning** of the effective tax
  year, **or any time during the preceding tax year**. The 2-month period runs from the day the tax year begins to the
  close of the day before the numerically corresponding day of the second month (no corresponding day → last day of
  that month). **Three published examples pin the math:** first year beginning Jan 7 → window Jan 7–**Mar 21**; prior
  tax year, effective Jan 1 → any time in the prior year through **Mar 15**; first year beginning Nov 8 → Nov 8–**Jan
  22** (an election made before the first day of the first tax year is NOT valid).
- **Item E (first year):** enter the **earliest** of first-had-shareholders / first-had-assets / began-doing-business;
  usually a short year not beginning Jan 1. Changing-year filers use the short-year beginning date (or the following
  year + Form 1128 attached/separate, "Form 1128" noted at item E).
- **Late relief (Rev. Proc. 2013-30; i2553 Relief for Late Elections):** top margin of page 1 = **"FILED PURSUANT TO
  REV. PROC. 2013-30"** (and, when attached to a late-filed 1120-S, its page-1 margin legend). Corporate path
  requirements 1–5: intended-S as of item E · fails solely for late filing · reasonable cause + diligence · **filed
  within 3 years and 75 days of item E** · consistent-reporting statements from all item-E-to-filing shareholders
  (column K satisfies this). The **6a–c alternative** lifts the 3yr75d cap (all reported consistently · ≥6 months
  since the first S-year return was filed · no IRS problem-notice within 6 months of that filing). Entity path =
  requirements 1–8 incl. the **Part IV representations**. Otherwise → **§1362(b)(5) letter ruling, $14,500 fee**
  (Rev. Proc. 2026-1 App. A (A)(3)(c)(i)). Consent/signature defects may instead ride **Rev. Proc. 2022-19 §3.03**
  (no PLR needed).
- **Consents (column K; i2553):** community-property spouses **both** consent (Rev. Proc. 2004-35 for the
  community-property-only spouse) · every tenant-in-common/joint tenant/tenant-by-entirety · minors by
  self/representative/parent · estates by executor · **ESBT: trustee + (if grantor trust) deemed owner** · **QSST:
  deemed owner** · other §1361(c)(2) trusts: the §1361(c)(2)(B) person. **Timing:** filed **before** item E → only
  day-of-election owners consent; filed **on/after** item E → everyone who held stock from item E through the
  election date. Disregarded-LLC-held stock → the owner (who must be an eligible shareholder).
- **Where to file (verified current 2026):** CT DE DC GA IL IN KY ME MD MA MI NH NJ NY NC OH PA RI SC TN VT VA WV WI →
  **Kansas City, MO 64999, fax 855-887-7734**; the rest → **Ogden, UT 84201, fax 855-214-7520**. Fax filing allowed
  (keep the original). Late elections may attach to the current/first 1120-S.
- **Acceptance:** determination generally within **60 days** (Q1 adds ~90); follow up at **2 months** (5 if Q1) via
  800-829-4933; the acceptable proofs-of-filing list. **Do not file the 1120-S before the election takes effect.**
- **End of election / re-election bar:** after termination or revocation, IRS consent is generally required to
  re-elect **before the 5th tax year** after the first termination year (§1.1362-5).
- **8832 boundary (both directions):** an eligible entity that timely elects S is **deemed classified** as a
  corporation — no Form 8832 filed; conversely 8832 is never used for an S election (WO-22's R/diagnostic already
  routes this way).

## Recent changes

**Form/instructions: none** — Rev. 12-2017 / 12-2020 are current (About-page's only development = the 2019 address
change, already in the printed table; live where-to-file page matches verbatim). **No OBBBA impact** (structural
§1362 election). **One superseded figure:** the item-Q1 user fee — printed **$6,200** (Rev. Proc. 2021-1 era) →
**$5,750** per Rev. Proc. 2026-1 App. A (A)(3)(a)(ii) (verified verbatim; year-keyed — re-verify each January).

---

## Proposed scope for the Gate-1 walk (compute vs defer)

1. **Eligibility diagnostics (the 8 tests)** — compute what the app can see: shareholder count (with the
   spouse/family aggregation caveat + item G), ineligible-shareholder-type and NRA screens from the shareholder
   records, ineligible-corporation screen, permitted-tax-year screen (F(2)/(4) → Part II gate). One-class-of-stock =
   preparer-asserted (diagnostic INFO, not adjudicated).
2. **The election-window calculator (§1362(b))** — compute the 2mo15d deadline from item E per the published
   counting rule (the three examples become pinned scenarios); classify timely vs late; late → the Rev. Proc. 2013-30
   path chooser (corporate 1–5 vs 6a–c vs entity path w/ Part IV) + the 3yr75d clock + the margin legend + the
   $14,500 PLR fallback diagnostic.
3. **Consent completeness** — compute the required-consent set timing rule (before vs on/after item E) and
   grid-completeness diagnostics (every J row needs K signature status, L, M, N; community-property both-spouses
   warning; trust-type → who signs).
4. **Part II routing + Part III/IV printing** — F(2)/(4) forces Part II O + (P|Q|R) completeness; Q1 → user-fee
   warning ($5,750, year-keyed) + conference box; R1 → Form 8716 pointer. QSST Part III per-trust print block
   (transfer-date ≤ election-date gate); Part IV auto-included on the entity late path. entity_types = **['1120S']**
   (the election creates the 1120-S filer; print-first, no MeF — Form 2553 is paper/fax only).
