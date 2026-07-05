---
type: project-decisions
project: sherpa-tax-rule-studio
last_updated: 2026-07-04
---

# DECISIONS — sherpa-tax-rule-studio

*Architectural and scope choices. Append-only log. Each entry is a decision that shouldn't be re-litigated without new information. If you find yourself reopening a decision, either add a new entry that overrides the old (and say why) or leave both so the history is visible.*

---

## How to use this file

Each decision gets a dated entry with: what was decided, why, what was considered instead, and what would change our mind. Never delete entries — if a decision is reversed, add a new one that supersedes it.

---

## 2026-07-04 — D-5: Spec approval (draft→approved) is source-controlled via a manifest, not a DB edit

**Decision:** A spec's approval state is recorded in **source control** — `specs/approved_specs.py`
(`APPROVED_FORMS`, one entry per Ken-signed-off form) — and applied to the DB by the
`approve_specs` management command, which `seed_all` runs as its final phase (5). Approval is
NEVER set by a one-off DB edit. A from-scratch rebuild (`seed_all`) therefore restores every
approval from the manifest. `approve_specs` also reports drift: manifest entries with no matching
form, and forms approved in the DB but absent from the manifest (which would be lost on rebuild).

**Context:** The `TaxForm.status` field (draft/review/approved/archived) already existed, and every
loader seeds the model default `draft` (verified: all 88 forms were `draft`). The July checklist
item "begin the draft→approved workflow" needs a way to mark Ken-approved specs. The 2026-07-04
reconstructability check ([reconstructability_check.md]) had just proved that any state living only
in Supabase (not reproducible from loaders) silently drifts and is lost on rebuild.

**Alternatives considered:**
- Flip `status` directly in the DB / via Django admin — rejected: approval would vanish on the next
  `seed_all` (loaders re-seed `draft`); it is exactly the "lives only in Supabase" anti-pattern the
  reconstructability check cleaned up.
- Have each loader set its own `status=approved` — rejected: scatters approval across ~60 loaders,
  couples a sign-off to a code edit of the spec loader, and gives no single audit of "what Ken
  approved." A central manifest is one diffable list.

**What would change our mind:** if approval needs per-version or per-jurisdiction granularity beyond
what `form_number` (+ optional `jurisdiction`) gives, extend the manifest entry schema. If the app
grows a UI-driven review workflow, the manifest becomes the export target of that UI rather than a
hand-edited file.

---

## 2026-07-04 — D-4: S3/S4 unblock campaign — Schedule A (8936) is a separate spec (key 8936_SCHA); OBBBA gates are first-class year-keyed gates

**Decision:** Authoring the four MeF-ATS-blocking specs (4835, 8835, 8936, Schedule A
(8936)), three sub-decisions: (a) **Schedule A (Form 8936) is exposed as its OWN RS form
under the canonical lookup key `8936_SCHA`** (not folded into the 8936 export), following
the `1120S_SCHL` convention — it is a distinct IRS form (Cat. 93602W, Attach. Seq. 69A),
per-vehicle, while 8936 aggregates. (b) **The OBBBA termination gates are encoded as
first-class, year-keyed, highest-precedence gates**, not buried in prose: 8936's
"acquired after 9/30/2025 → no credit" runs per-vehicle on Schedule A before any credit
math (`R-8936SA-OBBBA` / `D_8936_001`), and 8835's "construction begins before 2025"
runs per-facility (`R-8835-OBBBA` / `D_8835_001`); both cutoffs live in year-keyed dicts
(`OBBBA_ACQUIRED_CUTOFF`, `SEC45_BEGIN_CONSTRUCTION_CUTOFF`) so TY2026 forces a re-verify
rather than silently reusing 2025. (c) **Disputed dollar amounts are left UNPINNED and
flagged, not guessed** — the S4 new-vehicle tentative credit is blank on the scenario
form (it comes from the seller report), so the S4 test asserts the gates + routing and
carries the credit amount as `[VERIFY-ATS-KEY]`; the $3,750/$7,500 §30D(b) tiers are
cited to the statute, not to Form 8936 (which doesn't print them).

**Context:** Ken's campaign prompt directed authoring all four so the tts app can build
S3 (Form 4835) and S4 (8936 + Schedule A + 8835). The prompt supplied tts-authored notes
transcribed from the 2025 DRAFT forms; the Authoritative-Source Rule required re-verifying
against the FINAL 2025 forms + instructions before locking (done via two subagents that
read the final PDFs verbatim). The OBBBA (P.L. 119-21) energy-credit terminations are the
highest-risk items and TY-sensitive.

**Alternatives considered:**
- Fold Schedule A into the 8936 export (one lookup key) — rejected: the tts build computes
  per-vehicle Schedule A then aggregates; a separate spec mirrors that and matches the
  probed `8936_SCHA` key + the `1120S_SCHL` precedent.
- Encode the OBBBA cutoffs as inline constants for 2025 only — rejected: violates the
  year-keyed-constants rule; a 2026 return would silently reuse the 2025 gate (and TY2026
  the credits are gone entirely).
- Assume $7,500 for the S4 EV credit to make the test concrete — rejected: the notes and
  the form both say the tentative credit is seller-reported; guessing it would encode a
  likely-wrong number (the BMW i4 is import-assembled and may not qualify at all).

**Reasoning:** Separate-form modeling keeps the per-vehicle → aggregate flow honest and
reusable. First-class year-keyed gates make the season-critical OBBBA terminations
auditable and re-verify-forcing. Leaving disputed dollars unpinned honors the
"flag, don't guess" tax-law rule and pushes the resolution to the ATS answer key / engine
where it belongs.

**Would reconsider if:** the tts build finds the aggregation cleaner with Schedule A
folded into 8936; or the ATS answer key pins the S4 tentative credit (then update the S4
test from `[VERIFY-ATS-KEY]` to the confirmed amount).

---

## 2026-07-04 — D-3: Form 4835 loss path FULLY COMPUTED (not RED-deferred); SE-exclusion is a hard invariant

**Decision:** The Form 4835 (Farm Rental Income and Expenses) spec computes the full
net-loss path — §465 at-risk (Form 6198) THEN §469 passive (Form 8582, incl. the
$25,000 active-participation special allowance) — rather than RED-deferring a loss
the way Schedule F does. It integrates with the EXISTING RS `FORM_8582` (Sch E loader)
and `6198` (1120-S loader) specs; it does not re-author them. Two companion rulings in
the same unit: (a) a HARD SE-EXCLUSION INVARIANT — no 4835 amount (line 32 income,
line 34c loss) may ever enter the Schedule SE base (line 1a/2 or the farm-optional
gross farm income); `R-4835-SE-EXCLUSION` + `FA-1040-4835-05` + `D_4835_SE_GUARD`
enforce it (§1402(a)(1)); and (b) a material-participation FORM-SELECTION guard —
`D_4835_MATPART` routes a materially-participating filer to Schedule F.

**Context:** Ken directed the loss path be computed because Form 4835 is in the MeF
(Modernized e-File) test set: an e-filed 4835 with a deductible loss must carry the
correct line-34c value and the 8582/6198 linkage in the XML, so a RED-defer (which
Schedule F uses for its own passive/at-risk loss) would leave the MeF case untestable.
The discovery that both limiter forms already exist in RS made computing — not
deferring — the cheaper correct option.

**Alternatives considered:**
- RED-defer the 4835 loss (the Schedule F precedent) — rejected: leaves the MeF
  loss case uncomputable; and unlike Sch F (where 8582/6198 weren't yet wired) the
  limiter specs are already available to integrate.
- Re-author 8582/6198 inside the 4835 unit — rejected: duplicates existing specs and
  would fork the passive/at-risk machinery. The 4835 activity registers as an input
  activity into the shared computations instead (flow assertions are the contract).

**Reasoning:** Computing through the existing limiters gives MeF-grade correctness at
integration cost, not re-implementation cost. The SE-exclusion invariant is the form's
defining trait (its subtitle is literally "Income Not Subject to Self-Employment Tax")
and is exactly the wiring bug a copy-paste from the Schedule F SE feed would introduce
— so it is asserted, not just documented.

**Would reconsider if:** the FORM_8582 per-activity allocation (Parts IV-VIII) turns
out not to accept a farm-rental activity in the active-rental-RE bucket (walk item B),
or a future MeF schema change alters the 4835→Sch E line-40 / 8582 linkage.

---

## 2026-07-04 — D-2: 1041 Schedule I (AMT) RED-DEFERRED for season one

**Decision:** Do NOT author or build the Form 1041 Schedule I (Alternative Minimum
Tax — Estates and Trusts) compute for season one. Instead, wire a loud RED
diagnostic that fires when a trust return shows AMT indicators, telling the
preparer the AMT path is out of scope and must be handled manually. Build the
real Schedule I spec + compute later only if demand warrants. This is one of the
two "Ken rulings" recorded on the RULE STUDIO AUTHORING TRACK in
`tts-tax-app/SEASON_CHECKLIST.md`; the companion is D-1 (1065 core specs are
authored fresh from IRS primary sources, then the existing 35 compute formulas
are reconciled against each spec — never spec-from-code; every mismatch is a
logged Ken adjudication).

**Context:** The September 1041 authoring wave (spine → DNI/IDD/Sch B → Sch G /
K-1 / GA 501) has to fit the season-one runway. Schedule I is a large, low-frequency
surface for this firm's trust population, and building it correctly would consume
walk-and-reconcile time better spent on the DNI/IDD core that every fiduciary
return touches.

**Alternatives considered:**
- Build Schedule I fully in season one — rejected: cost far exceeds the frequency
  it would actually be exercised at, and it crowds out the DNI/IDD spine.
- Silently omit it (no diagnostic) — rejected: violates the never-silent rule; a
  trust with AMT indicators would produce a wrong return with no warning.

**Reasoning:** A RED-deferred diagnostic gives the correctness guarantee (no
silently-wrong AMT return) without the build cost, and defers the real work to a
point where observed demand can justify it. Mirrors the established RED-defer
pattern used elsewhere in the suite (e.g. RRTA on 8959).

**Would reconsider if:** Trust returns with AMT exposure show up often enough in
the TaxWise regression bed to justify the build, or a state/federal change forces
Schedule I into a common path.

---

## 2026-04-27 — <Short decision title>

**Decision:** <what we chose>

**Context:** <the problem or question that forced a choice>

**Alternatives considered:** <what else was on the table and why we passed>

**Reasoning:** <why this option won>

**Would reconsider if:** <what new information would flip this>

---

## 2026-04-27 — <Short decision title>

**Decision:**

**Context:**

**Alternatives considered:**

**Reasoning:**

**Would reconsider if:**

---

<!-- Append new entries at the top. Older decisions remain below. -->
