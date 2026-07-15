# Form 8879 / Form 8878 — Source Brief (WO-33, tts s90 draft-to-gate)

*Drafted 2026-07-15. Greenfield: RS lookups 404 x4 confirmed 2026-07-15
(`lookup/{8879,FORM_8879,8878,FORM_8878}/export/`). The e-file SIGNATURE-AUTHORIZATION
print pair — the next NEW autonomous item per BUILD_ORDER after the six-leg dispatch
set landed (s85-s89).*

---

## Sources (all verbatim, all fetched fresh 2026-07-15)

1. **Form 8879 (Rev. January 2021)** — "IRS e-file Signature Authorization",
   Cat. No. 32778X, OMB 1545-0074. CONTINUOUS-USE revision; instructions are
   self-contained on page 2 (no separate i8879). About page checked: current
   revision = 0121, Recent Developments = "None at this time." (page last
   reviewed 30-Mar-2026).
2. **Form 8878 (2025)** — "IRS e-file Signature Authorization for Form 4868 or
   Form 2350", Cat. No. 32777M, "Created 4/17/25". YEAR-DATED (unlike the 8879)
   — the s48 face-drift class applies; a 2026 revision will re-date the jurat
   text ("tax year ending December 31, 2025" is printed into Part II verbatim).
   About page: current = 2025, Recent Developments = "None at this time."
3. **Pub. 1345** (current PDF, 45 pp) — the handbook BOTH faces cite in their
   Part III jurats. Signing an Electronic Tax Return / Electronic Signature
   Methods / IRS e-file Signature Authorization (Forms 8878 and 8879) /
   Electronic Signature Guidance sections (pp. 14-18) read in full.
4. **MeF (local, already-cached)**: efileTypes.xsd 2025v5.3 (`PINCodeType`,
   `PINEnteredByType`), ReturnHeader1040x.xsd (`PractitionerPINGrp`,
   `SelfSelectPINGrp`, `PINTypeCd`, `JuratDisclosureCd`, PIN/date elements),
   and the 1040 Business Rules CSV 2025v5.3 — 47 signature-family rules pulled
   (F1040-310..318/405/525/526, IND-021..032, IND-054..059, IND-418/433/524,
   IND-664..667, IND-672..680).

## The structural headline

**Neither form transmits. Both are ERO-RETAINED print artifacts** — the face
says "ERO Must Retain This Form — Don't Submit This Form to the IRS Unless
Requested To Do So." There is NO MeF document, NO ReturnData slot, NO new
submission family. The ELECTRONIC mirror of these forms is the Return Header
signature block tts ALREADY transmits (PINTypeCd / JuratDisclosureCd /
PractitionerPINGrp / signature PINs — ATS-proven across all seven accepted
scenarios). The tts leg is therefore: a persistent signature-input surface +
print (two AcroForm units) + diagnostics that tie the printed authorization to
the header PIN data + extract/transmit gating. The print-only V/ES recipe
(s87) applies, with a HEADER tie instead of a payment tie.

## Form 8879 — the when-required chart (face verbatim, 4 rows)

| IF the ERO is... | THEN |
|---|---|
| Not using Practitioner PIN method, taxpayer enters own PIN | DON'T complete 8879 |
| Not using Practitioner PIN method, authorized to enter/generate taxpayer's PIN | Parts I and II |
| Using Practitioner PIN method, authorized to enter/generate | Parts I, II, and III |
| Using Practitioner PIN method, taxpayer enters own PIN | Parts I, II, and III |

**The derivation: 8879 required iff (Practitioner PIN method) OR (ERO enters or
generates the taxpayer's PIN).** Pub 1345 states the PP half directly:
"taxpayers must always sign a completed signature authorization form... even if
they enter their own PINs." Part III exists ONLY on the PP rows.

- Scope: 1040, 1040-SR, 1040-NR, 1040-SS, 1040-X — **original AND amended** —
  tax years 2019+.
- Part I (whole dollars): 1 AGI · 2 Total tax · 3 Federal income tax withheld
  from Form(s) W-2 and Form(s) 1099 · 4 Refund · 5 Amount owed. **Note (face):
  Form 1040-SS filers use line 4 ONLY** (lines 1-3, 5 blank).
- PIN hygiene: taxpayer PIN = five digits, NOT all zeros. Part III = ERO's
  six-digit EFIN + five-digit self-selected PIN (11 digits), not all zeros.
- SID: 20-digit Submission Identification Number at the top — entered AFTER
  filing, **or associate Form 9325 with the retained 8879** (9325 need not be
  physically attached; it inherits the 8879 retention rules).
- **Timing (face caution + Pub 1345): the ERO must RECEIVE the completed,
  signed 8879 BEFORE the return is transmitted (or released for
  transmission).** The ERO may key the PIN into the record before the taxpayer
  signs, but transmission waits for the signature.
- **Retention: 3 years from the return due date or the IRS received date,
  whichever is later**; electronic retention OK per Rev. Proc. 97-22.
- Authentication Record (NON-PP only): taxpayer date of birth + prior-year AGI
  or prior-year PIN (or both) **from the ORIGINALLY FILED prior-year return —
  never an amended amount, never a math-error-corrected amount**. PP method:
  none of that is required (the face says so; MeF mirrors via IND-025/026
  which demand PriorYearAGI/PIN/IP-PIN only for the Self-Select PIN types).
- MFJ: split authorization is fine (one spouse authorizes the ERO, the other
  self-enters); **entering an ABSENT spouse's PIN is forbidden**.
- Corrected copy: provide one if the return changes after signing. **Pub 1345
  tolerance: a NEW declaration/signature is required only when the change
  exceeds $50 of Total income/AGI or $14 of Total tax / withholding / refund /
  amount owed.** Inside the tolerance, no re-sign.
- Signatures: taxpayer signs HANDWRITTEN or ELECTRONIC (if the software
  supports it); the ERO may sign via rubber stamp / mechanical device /
  software (Notice 2007-79) — that alternative NEVER extends to the taxpayer.
- Pre-signed authorizations: allowed ONLY when the taxpayer brings a completed
  return to the ERO; ERO enters the paper return's line items on the 8879
  first, and may use it only if the e-version matches the paper entries.
- Pub 1345 stockpiling: originate as soon as possible after signature;
  waiting >3 calendar days once everything is in hand = stockpiling.
- Self-Select ineligibility (Pub 1345 + IND-674/675/679/680): primary under 16
  who never filed; secondary under 16 who didn't file the prior year — those
  returns must use the Practitioner PIN method (or paper).

## Form 8878 — the when-required chart (face verbatim, 5 rows)

| IF e-filing... | THEN |
|---|---|
| 4868 + EFW + taxpayer enters own PIN + NOT PP method | DON'T complete 8878 |
| **4868 + taxpayer NOT authorizing an EFW** | **DON'T complete 8878** |
| 4868 + EFW + ERO enters/generates PIN + NOT PP method | Parts I and II |
| 2350 + ERO enters/generates PIN | Parts I and II |
| 4868 + EFW + PP method | Parts I, II, and III |

**The load-bearing negative: a 4868 WITHOUT an electronic funds withdrawal
NEVER needs an 8878** — the exact print-side mirror of the s88 4868 unit's
R0000-098 story (a no-payment e-filed 4868 carries NO signature at all). The
8878 gate composes: EFW elected AND (PP method OR ERO enters/generates PIN).

- Part I: check ONE box only. Line 1 = Form 4868, amount paying **from 4868
  line 7**. Line 2 = Form 2350: 2a extension-until date (2350 line 1), 2b
  amount paying (2350 line 5).
- **Part III is "Practitioner PIN Method for Form 4868 Only" — a 2350
  authorization NEVER reaches Part III** (face verbatim, both the banner and
  the Part III title).
- Face caution: the 8878 is NOT itself an extension application — the 4868 or
  2350 must still be filed.
- Non-PP + EFW: same DOB + prior-year-AGI-or-PIN authentication as the 8879
  (originally-filed amounts only).
- Everything else mirrors the 8879 verbatim: 5-digit non-zero PINs, EFIN+PIN
  Part III, SID/9325, sign-before-transmit, 3-year retention (Rev. Proc.
  97-22), MFJ split-authorization + absent-spouse bar, corrected copy,
  handwritten-or-electronic taxpayer signature, Notice 2007-79 ERO stamps.

## Electronic-signature framework (Pub 1345 — recorded as FACTS, not app scope)

Optional e-signing of the 8878/8879 requires the software to record: digital
image of the signed form; date/time; taxpayer IP + login (REMOTE only);
identity-verification results (KBA pass); signing method/audit trail — all
producible to the IRS on request. Identity proofing to NIST SP 800-63 L2 +
KBA. In-person: government photo ID inspection (waivable on a multi-year
relationship); remote: record checks mandatory. **KBA failure x3 -> a
HANDWRITTEN signature is required.** Remote handwritten forms returned by
mail/fax/email/website are NOT "electronic signatures" and need none of this.
Office reality: in-person/handwritten — the framework is future portal work.

## MeF ties (the header block the print mirrors — all already built in tts)

- `PINCodeType` = {Practitioner, Self-Select Practitioner, Self-Select
  On-Line}. In an ERO product only the first two occur (Self-Select On-Line
  is the self-filer path; IND-673 FORBIDS PractitionerPINGrp with it, and it
  is unreachable from tts — tts SignatureInfo defaults pin_type_cd
  "Practitioner").
- IND-672: PINTypeCd Practitioner OR Self-Select Practitioner -> the header
  MUST carry PractitionerPINGrp (EFIN + ERO 5-digit PIN = the 8879 Part III
  content).
- IND-025/026 (+027/028 spouse): Self-Select types + BirthDt -> PriorYearAGI
  or PriorYearPIN or IP-PIN required; IND-031/032 = the e-File-database match
  (the 8879's Authentication Record paragraph, rule-for-rule).
- IND-056/057: a signature PIN requires PINEnteredByCd {Taxpayer, ERO} — the
  element that decides the 8879's "who entered it" chart row. IND-058/059:
  signature PIN -> signature DATE required (the 8879's date lines).
- IND-418 (MFJ SpousePINEnteredByCd), IND-433 (non-MFJ primary PIN required),
  IND-054/F1040-405 (MFS/HoH: no spouse PIN), F1040-310..318 (MFJ PIN
  presence with death/combat-zone/special-condition carve-outs).
- IND-664..667: SSN appearing more than once in the e-File database bars BOTH
  Self-Select types (PP method still flies). IND-674/675/679/680 = the
  under-16 bars above.
- 4868 side (s88, already pinned in tts): the jurat/PIN ladder engages only
  when a payment record rides (R0000-098; two-value jurat enum by PIN type;
  FPYMT-052-02 EFW tie) — the 8878's chart row 2 is the print-side same fact.

## Proposed v1 scope (the Gate-1 walk, W1-W4)

- **W1 — the 8879 need-gate + Part I**: required iff PP method OR
  ERO-entered/generated PIN; Parts I/II/III by chart row; Part I amounts off
  the 1040 face (whole dollars); 1040-SS line-4-only fact (app boundary);
  original + amended coverage.
- **W2 — signature mechanics**: 5-digit non-zero PINs; EFIN+PIN Part III;
  sign-BEFORE-transmit; SID-after-filing or 9325 association; 3-year
  retention; MFJ split/absent-spouse; corrected-copy + the $50/$14 re-sign
  tolerance; stockpiling clock; under-16 + duplicate-SSN self-select bars;
  prior-year-originally-filed authentication for non-PP.
- **W3 — the 8878 gate**: EFW AND (PP OR ERO-entered); the no-EFW-never
  negative (the s88 mirror); Part I one-box + the 4868-line-7 tie; the
  2350 arm (Parts I+II, never III) as a stated APP BOUNDARY (no 2350 in tts).
- **W4 — ties + print**: entity_types ['1040']; print-only pair (no MeF
  document BY DESIGN — the header already carries the electronic signature);
  diagnostics tie the printed forms to the header PIN data; extract/transmit
  gating recommendation; e-signature framework recorded as facts (portal
  future); year-watch on the 8878 (year-dated face).

## Seams FLAGGED for the walk (not resolved)

1. **8879 line 3 mapping.** The face says "Federal income tax withheld from
   Form(s) W-2 and Form(s) 1099" — literally 1040 25a+25b. But the Rev-01-2021
   caption predates the current 25c contents (W-2G box 4, 8959), and Part I is
   otherwise the return's own refund/owe math (which runs through 25d).
   *Recommendation: map line 3 = 1040 line 25d (total withholding)* so Part I
   stays self-consistent (L1-L3 explain L4/L5); divergence from the literal
   reading only when 25c != 0. Ken rules.
2. **1040-X arm.** The 8879 covers amended returns; Part I then carries the
   1040-X column-C world (AGI 1C, total tax 11C, refund 22, owed 20).
   *Recommendation: encode as a rule arm; the tts leg prints from the existing
   1040-X unit's computed values.*
3. **Extract/transmit gating.** Pub 1345 puts the signed-8879 requirement
   before TRANSMISSION, not before XML composition. House posture is
   refusal-beats-fabrication at the extract bridge. *Recommendation: extract
   refuses when the required authorization has no signed date (naming the
   sign-first rule); revisit at S-17g when the transmit loop becomes real.*
4. **Signature-date storage.** The $50/$14 tolerance needs the SIGNED-AT
   amounts retained to compare against later recomputes. *Recommendation: the
   tts leg snapshots Part I at signing; the corrected-copy diagnostic compares
   live vs snapshot.*

## Boundaries (stated, not specced)

- 1040-SS / 1040-NR / 2350 returns: no such modules in tts — the 8879's
  1040-SS line-4 fact and the 8878's 2350 arm are encoded as form facts; the
  tts leg implements the 1040/1040-X + 4868 paths only.
- Remote e-signature/KBA infrastructure: facts only (sherpa-portal future).
- Form 9325 (the SID-association alternative): separate S-22b triage item —
  the spec references it, does not define it.
- The ERO/preparer identity data (EFIN, firm name) comes from the existing
  Preparer records (s84 ADMIN-gated) — not re-specced here.

## Year-watch register

- Form 8878 is YEAR-DATED — re-verify the 2026 face when published (~Oct-Nov
  2026); the Part II jurat embeds the tax year verbatim.
- Form 8879 is continuous-use Rev. 01-2021 — watch About-page Recent
  Developments (currently none).
- Pub 1345 signature chapter: re-verify at each annual reissue (the $50/$14
  tolerance and the 3-day stockpiling clock live there, not on either face).
