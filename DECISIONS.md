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

## 2026-07-05 — D-10: 1041 module (S-11/WO-09) v1 scope — core 4 + ESBT computed, FULL distribution engine, cap-gains-in-DNI direct-entry, GA 501 resident-only, Form 5227 spun off as its own leg

**Decision:** The greenfield federal 1041 fiduciary module (S-11 spine → DNI/IDD/Sch B → Sch G → K-1 →
GA 501) v1 scope, locked at the 2026-07-05 Gate-1 scope walk (AskUserQuestion, 4 + 1 follow-up):
- **(Q1) Entity types:** COMPUTE the core four (decedent's estate, simple trust, complex trust, qualified
  disability trust) fully + COMPUTE the **ESBT** S-portion separate-rate worksheet (top trust rate → Sch G
  Part I line 4). Model **grantor-type trust** as structure + the grantor-letter reporting path (NO K-1,
  dollars on an attachment). **Pooled income fund** = recognized entity type, routed to the Form 5227 leg
  (below). **Bankruptcy estate (ch. 7/11)** = RED-defer diagnostic (it is essentially an individual 1040).
- **(Q2) Distribution engine = FULL:** COMPUTE the §662 two-tier allocation (first-tier line 9 / second-tier
  line 10, DNI applied tier-1-first), the §663(c) separate-share DNI, the §663(b) 65-day election (Question 6
  checkbox), and proportional character retention of each DNI class to beneficiaries. The most correct
  subchapter-J engine; the heaviest reconcile leg.
- **(Q3) Capital gains IN DNI = direct-entry + diagnostic:** preparer enters Schedule B line 3 (gains
  attributable to income / treated-as-distributed); a diagnostic surfaces the three Reg. §1.643(a)-3(b)
  circumstances so the determination is documented, not silent. Default is corpus-excluded (§643(a)(3)).
  Chosen because inclusion hinges on the governing instrument + local law + the fiduciary's reasonable
  discretion — data the spec cannot read.
- **(Q4) GA Form 501 = resident-only v1:** COMPUTE the full-year resident 501 (federal 1041 Adjusted Total
  Income line 17 → beneficiary subtraction at 501 L4 → flat **5.19%** → $1,350/$2,700 exemptions → Sch 5/6
  credits). RED-defer the Schedule 4 nonresident source allocation AND the §168(k)/§179 GA-nonconformity
  add-backs to a later leg. (Diverges from the GA-700 MAXIMAL choice — a fiduciary book skews resident, and
  GA Form 501 has no dedicated depreciation line; the add-back would ride generic Sch 2 "Other" under §48-7-27.)
- **(follow-up) Form 5227 = its own dedicated leg:** author the split-interest-trust module (PIF + charitable
  remainder CRAT/CRUT + charitable lead trusts, incl. the §664(b) four-tier character-ordering regime) as a
  SEPARATE authoring leg WITH its own focused research pass + source brief — NOT folded inline. The §664 CRT
  distribution regime is a distinct body of law that earns verbatim source verification of its own.
- **Pre-decided (not walked):** Schedule I AMT = RED-defer diagnostic (D-2, unchanged); K-1 (Form 1041) full
  verbatim code transcription of boxes 9/11/12/13/14 (the 1065-K-1 precedent); form-key consolidation =
  one **`1041`** form (page-1 + Schedule B + Schedule G, tightly coupled: L18 IDD←Sch B L15, L24 tax←Sch G L9)
  + separate **`SCHEDULE_K1_1041`** + **`GA501`**; OBBBA §1062 (Form 1062 farmland installment, L25b/Sch G 18c) =
  structure + flag, low frequency.

**Context:** BUILD_ORDER S-11, the greenfield Sept 1041 rock (~70 trust returns, Ken's specialty, Apr 15
deadline). RS-first mode: enumerate the set, gap-check, author + Gate-1-approve all gaps, THEN dispatch the
tts app build. All TY2025 constants verified verbatim against FINAL IRS/GA sources in [f1041_source_brief.md]
(2025 Form 1041 Created 10/28/25; i1041 Mar 5 2026; 2025 Sch K-1; GA Form 501 Rev. 07/09/25). Rev. Proc.
2025-32 confirmed to be the TY2026 procedure — 2024-40 governs TY2025.

**Alternatives considered:** All-9-entity-types (rejected — PIF/bankruptcy are very low frequency; PIF is
better served by the dedicated 5227 leg). Core-IDD-only distribution engine (rejected — Ken wanted the full
tier/separate-share/65-day, his specialty). Compute cap-gains-in-DNI from structured flags (rejected — bakes
in an instrument-specific judgment that could mislead). GA 501 maximal like GA-700 (rejected for v1 — fiduciary
book skews resident, no dedicated GA depreciation line). Full 5227 inline (rejected — roughly doubles the
module and mixes two regimes; gets its own leg instead).

**What would change our mind:** if the forms-usage report shows ESBT/grantor/bankruptcy or nonresident GA
trusts are common, upgrade those from defer/structure to compute. If the §663(c) separate-share or §662
multi-tier compute proves to need per-share data the spec can't reach, fall back to structured-diagnostic for
those sub-legs (a reconcile-leg call). Re-verify ALL constants at TY2026 (OBBBA §67/§68 bite for years after
12/31/2025; the 2026 breakpoints are already known — see the brief).

---

## 2026-07-05 — D-9: SC1065 + SC1120S v1 — BOTH authored; SC PTET = the §12-6-545(G) 3% ATB entity election (owner EXCLUSION, not credit); §179 = indexed $1.25M/$3.13M (Reading A)

**Decision:** Extend the GA-700 + PTET work to Georgia's neighbors (Ken: "states adjacent to
Georgia" — the individual returns AL/NC/SC are already done, so the frontier is the pass-through
*entity* returns + PTET). Ken picked **SC pass-through + PTET**; the 2026-07-05 walk (4
AskUserQuestion) locked v1 as: (Q1) **author BOTH SC1065 (partnership) and SC1120S (S-corp)** this
session in one loader (`load_sc_passthrough.py`), SC1065 being the cleaner PTET vehicle and ~80% of
its SC-K/apportionment/I-435 engine ported to SC1120S; (Q2) **COMPUTE** the §168(k) bonus add-back
structure (year-1 add-back + remaining-life SC-basis subtraction) AND the §179 conformity delta,
direct-entering the asset-level SC-4562 figures the engine can't reach (GA-700 (B) precedent — Ken
is a depreciation CPA); (Q3) the SC §179 2025 cap = the **INDEXED $1,250,000 / $3,130,000**
(Reading A: conformed IRC §179 incl. its indexing provision; Rev. Proc. 2024-40), NOT the
conservative 2024 $1,220,000/$3,050,000 — matching the SC1040 pin; (Q4) **COMPUTE** apportionment
methods 1 (sales-only, TPP dealers) & 2 (gross-receipts, service/financial) via a business-type
selector (4 decimals) + the 5% nonresident withholding with the full exemption set (residents /
I-309 / composite / 501(a) / entity-taxed ATB), **RED-defer** special/individualized apportionment
+ the composite return (I-348/I-338) + the SC1120S multi-state license-fee apportionment + Schedule
D Annual Report. Structure/constants verified against the FINAL 2025 SCDOR sources (I-435 Rev.
1/30/25; SC1065 Rev. 6/18/25; SC1120S Rev. 6/17/25; I-335 Rev. 6/17/25; SC1120I; §12-6-545) — see
[sc1065_source_brief.md].

**Context:** SC's PTET is NOT a GA-700 clone. It is the **Active Trade or Business (ATB) elective
entity-level tax** (§12-6-545(G), Act 61 of 2021), computed on **Form I-435** at a **flat 3%** on
**active trade or business income ONLY** (excludes passive/investment income, capital gains,
§707(c) service payments). The election is **annual and NON-BINDING** (contrast GA's irrevocable
5.19%), a page-1 checkbox. The owner side is an **EXCLUSION, not a credit** (§12-6-545(G)(3)): the
owner SUBTRACTS the entity-taxed amount on **I-335 line 6** (partner ← SC1065 K-1 line 14;
shareholder ← SC1120S K-1 line 13). Entity-taxed ATB is also exempt from the 5% nonresident
withholding (SC1065 L6 = L1 − L2). SC1120S additionally carries a general **5%** SC income tax on
non-ATB net (L9) and a **license fee** (capital × .001 + $15, min $25) with no partnership analog.

**Divergence from precedent (called out):** GA-700's PTET is 5.19%, irrevocable, on the entity's
whole GA taxable income, with a PTEDED/PTEADD owner subtraction/addition on Form 500. SC's is 3%,
annual/non-binding, on ATB income only, with the owner exclusion via I-335 L6. The §179 Reading-A
pin ($1.25M/$3.13M) is **not SCDOR-stated** (the booklets defer to conformed IRC §179) — cited to
Rev. Proc. 2024-40 pending SCDOR confirmation, and stale if **H.3368** (pending) conforms SC to
OBBBA mid-season.

**What would change our mind:** if H.3368 is enacted, the §179 figures jump to $2.5M/$4M and bonus
treatment changes — all depreciation/§179 logic is stale until re-verified (W2). If an SCDOR source
later pins a different 2025 §179 figure, switch Reading A → the stated figure. If the ATB
active/passive segregation (I-435 Col C, W4) needs to be computed rather than direct-entered, that
is a later reconcile-leg call. SC1120S multi-state Schedule G/E/H apportionment + the license-fee
apportionment were RED-deferred for v1 and can be built if demand warrants.

---

## 2026-07-05 — D-8: GA-700 v1 scope is MAXIMAL — full PTET compute (5.19% entity-level), §179 delta computed, Schedule 4 + 4% NRW computed

**Decision:** The GA Form 700 (Georgia partnership return, TY2025) v1 spec — the **1st partnership-entity
state return** in RS (GA600S S-corp + GA Form 500 individual precede it) — is scoped MAXIMAL per Ken's
2026-07-05 walk (4 AskUserQuestion decisions, all recommended): (A) **COMPUTE the full PTET path** (HB
149 / §48-7-21) — the elective entity-level tax = GA taxable income × **5.19%** (Sch 1 L7), gated on the
Form 700 page-1 election checkbox, plus the owner-side **PTEDED (Form 500 Sch 1 L12 subtraction) /
PTEADD (L5 addition)** mechanics and the credits-and-NOLs-stay-with-the-entity rules; (B) **COMPUTE the
§179 GA-limit difference** (GA **$1,050,000/$2,620,000**, not the federal OBBBA $2.5M/$4M) + model the Sch
5 L7 (federal-depr add-back) / Sch 6 L4 (GA-depr subtraction) structure, and **direct-entry** the
asset-level GA Form 4562 depreciation figures (the MACRS recompute the engine can't yet reach); (C)
**COMPUTE Schedule 4 partner allocation** (resident reports full share / nonresident reports GA-apportioned
+ allocated, with guaranteed-payment handling — the IT-711 p.13 worked example is the test oracle) + the
**4% nonresident withholding** (§48-7-129, <$1,000-share exemption, displaced when PTET is elected); (D)
**direct-entry** Schedule 10 credits + intangible/REIT add-backs, **RED-defer** GA NOL (Sch 9, 80% limit),
composite return (IT-CR), the UET underpayment penalty (Form 600UET, incl. its 5.75% prior-year quirk),
and credit pass-through allocation (Sch 11). Structure/constants verified against the FINAL 2025 GA DOR
sources (Form 700 Rev. 09/11/25; IT-711 booklet; HB 149 FAQ; Reg. 560-7-3-.03) — see [ga700_source_brief.md].

**Context:** August RS state track ("GA-700 + PTET"). GA Form 700 starts from FEDERAL partnership income
(Sch 8 ≈ federal Sch K), applies GA additions/subtractions (Sch 5/6), apportions by a **single
gross-receipts factor** (Sch 7, 6 decimals — the GA600S loader's "3-factor" note was STALE), and taxes at
the flat 5.19% only when the PTET election is made. PTET is the headline reason to build GA-700 now (the
federal SALT-cap workaround). Ken is a depreciation CPA, hence (B) computes the §179 delta.

**Divergence from precedent (called out):** the GA600S loader (`load_remaining_1120s.py`) records the PTET
rate as **5.49%** and apportionment as "property/payroll/sales" 3-factor — BOTH stale. GA-700 pins the
DOR-primary **5.19%** (2025) and the single gross-receipts factor. GA's PTET base is a **single
entity-level number** (federal taxable income with C-corp limits → §48-7-27 GA adjustments → §48-7-31
apportionment), NOT a resident/nonresident split (correcting the initial framing).

**What would change our mind:** if the GA-4562 asset-level recompute is needed for a correct return the
spec can't reach, (B)'s depreciation-subtraction stays direct-entry (as scoped). If the 2025 GA conformity
bill (not yet posted — §10 flag 1) moved the §179 figures or the conformity date, those constants are
stale until re-verified. If GA600S later needs the same 5.19%/single-factor correction, treat this as the
precedent (its 5.49%/3-factor is a logged reconstructability-adjacent drift, not authority).

---

## 2026-07-04 — D-7: NC D-400 v1 scope is MAXIMAL — resident + Schedule PN, the 85% bonus/§179 add-back is COMPUTED, Schedule S subtractions modeled structured

**Decision:** The NC D-400 (North Carolina individual, TY2025) v1 spec — the 4th state individual spec
after GA Form 500, SC1040, AL Form 40 — is scoped MAXIMAL per Ken's 2026-07-04 walk (4 AskUserQuestion
decisions, all recommended): (A) compute the full-year **resident** D-400 AND **Schedule PN** (part-year/
nonresident taxable-percentage proration → D-400 line 13 → line 14 = line 12b × the PN decimal); (B)
**COMPUTE** the current-year depreciation add-back — 85% of federal bonus depreciation (Schedule S Part A
line 3) + 85% of the IRC §179 excess over NC's **$25,000/$200,000** limits (Part A line 4) — and
**direct-entry** the 20% prior-year (2020-2024) recovery installments (Part B lines 23a-e/24a-e), which
need historical records the spec cannot reach; (C) **model L18 (US-obligation interest) / L19 (SS/RR) /
L20 (Bailey Settlement) / L21 (military retirement) as structured** Schedule S Part B line items with
eligibility diagnostics, not a single collapsed total; (D) **direct-entry** D-400TC credits (L16) +
consumer use tax (L18) + contributions (L30-32), and **RED-defer** Schedule PN-1, amended-return lines
(L22/L24, Schedule AM), the L26e estimated-tax underpayment interest (Form D-422), and the NC NOL (L39).
Structure/constants verified against the FINAL 2025 NCDOR PDFs (Form D-400 & Schedule S rev "Web-Fill
9-25"; D-401 booklet 2025) — see [nc_d400_source_brief.md]; **flat rate 4.25% (0.0425)**, standard
deduction $12,750/$25,500/$19,125, child-deduction AGI-banded table ($3,000→$0), conformity frozen at
**Jan 1, 2023 (OBBBA not adopted)**.

**Context:** August RS state track ("NC D-400 next" after SC1040 + AL Form 40). NC starts from FEDERAL
AGI (like GA-500; contrast SC's federal-taxable-income start and AL's from-scratch build) and is a FLAT
rate — the return's complexity is in the Schedule S conformity add-backs and the child-deduction table.
Ken is a depreciation CPA, hence (B) computes the add-back rather than deferring it — consistent with
SC1040 D-6's choice to compute the §168(k) add-back and diverging from GA-500 W1's direct-entry.

**Divergence from precedent (called out):** GA-500 v1 took depreciation decoupling as preparer
direct-entry (GA-500 W1). NC D-400 (B), like SC1040 (B), **computes** the current-year add-back. Unlike
SC (a single §168(k) bonus add-back), NC needs BOTH the 85% bonus add-back AND the 85% §179-excess
add-back (federal §179 − NC §179 at $25k/$200k), plus recognition that the 20% recovery installments are
a separate, historical-record-dependent direct-entry surface.

**What would change our mind:** if the add-back compute turns out to need asset-level data the spec
can't reach cleanly (the §179-excess needs both the federal and NC §179 figures), (B) may fall back to
direct-entry for v1 with the compute deferred to the depreciation-engine integration — a Ken call at the
reconcile leg. If NC issues a mid-season conformity update (the booklet warns to check), the 85%/limits/
rate constants are stale until re-verified.

---

## 2026-07-04 — D-6: SC1040 v1 scope is MAXIMAL — full resident + Schedule NR, and the §168(k) depreciation add-back is COMPUTED

**Decision:** The SC1040 (South Carolina individual, TY2025) v1 spec — the 2nd state individual
spec after GA Form 500 — is scoped MAXIMAL per Ken's 2026-07-04 walk (4 AskUserQuestion decisions):
(A) compute the full-year **resident** form AND **Schedule NR** (part-year/nonresident 3-column
SC-source proration → Sch NR line 48 → SC1040 line 5); (B) **COMPUTE** the line-e IRC §168(k)
bonus-depreciation add-back (SC non-conformity), NOT preparer direct-entry; (C) compute the full
**retirement / military / age-65 deduction stack** (the interacting reductions — SC's center of
gravity); (D) **RED-defer** the niche items (I-335 active-trade 3% election L8/line-l, SC4972
lump-sum L7, catastrophe-savings L9) each as a "prepare manually" diagnostic, and **direct-entry**
SC1040TC other credits (L13). Structure/constants verified against the final 2025 SC DOR PDFs
(SC1040 Rev. 4/21/25; SC1040TT Rev. 6/17/25) — see [sc1040_source_brief.md]; top rate 6% (down from
6.4%), 3 brackets 0/3/6% at $3,560/$17,830, $642 rate-schedule constant.

**Context:** August RS state track ("SC1040 — CC drafts, Ken walks — GA-500 pattern"). SC starts from
FEDERAL TAXABLE INCOME (contrast GA-500's federal AGI start). Ken is a depreciation CPA, hence the
choice to COMPUTE the §168(k) add-back rather than defer it.

**Divergence from precedent (called out):** GA-500 v1 took its depreciation/conformity decoupling as
**preparer direct-entry** (GA-500 W1). SC1040 (B) instead **computes** the §168(k) add-back. This
requires pinning SC's TY2025 IRC conformity date + the bonus add-back formula (federal depr − depr-
without-bonus), §179 conformity, and the future-year subtraction/basis-difference mechanics — a
follow-up research pass was dispatched 2026-07-04 to verify these against SC sources before authoring.

**What would change our mind:** if SC's conformity/bonus mechanics turn out to need asset-level data
the spec can't yet reach cleanly, (B) may fall back to direct-entry for v1 (matching GA-500) with the
compute deferred to the depreciation-engine integration — a Ken call at the reconcile leg.

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
