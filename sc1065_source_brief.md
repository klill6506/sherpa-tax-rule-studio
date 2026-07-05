# SC1065 + SC PTET (South Carolina Partnership Return + entity-level ATB tax) — Source Brief (TY2025)

*Prepared 2026-07-05 to kick off the **SC1065 + SC PTET** authoring campaign (adjacent-state
track — extends GA-700 + PTET to Georgia's neighbors; Ken picked "SC pass-through + PTET").
This is a TRANSCRIPTION AID / reconcile map — **NOT a spec and NOT authorization to seed.**
Per D-1, the spec is authored FRESH from SC DOR primary sources; every constant below was
VERIFIED against the FINAL 2025 SCDOR PDFs by a research pass 2026-07-05 (never memory). The
confidence flags in §7 mark the handful that need a last look before locking. GA-700
(`load_ga700.py`) is the direct partnership+PTET structural precedent; SC1040
(`load_sc1040.py`) supplies the reusable SC conformity/depreciation authority sources.*

---

## 1. Primary sources (all dor.sc.gov, TY2025 FINAL — revision dates confirmed on each face)

- **I-435 (Rev. 1/30/25)** — Active Trade or Business Income Reduced Rate Computation (the
  ENTITY-LEVEL PTET computation form) — https://dor.sc.gov/sites/dor/files/forms/I435.pdf
- **SC1065 (Rev. 6/18/25)** — 2025 Partnership Return —
  https://dor.sc.gov/sites/dor/files/forms/SC1065_2025.pdf
- **SC1120S (Rev. 6/17/25)** — S Corporation Income Tax Return (deferred; the SC1065 ports ~80%) —
  https://dor.sc.gov/forms-site/forms/sc1120s.pdf
- **I-335 / 335A / 335B (Rev. 6/17/25)** — the OWNER-side 3% ATB election (shows the exclusion
  mechanic) — https://dor.sc.gov/sites/dor/files/forms/I335_2025.pdf
- **SC1120I** — 2025 C & S Corporation Instructions ("What's New — Conformity") —
  https://dor.sc.gov/sites/dor/files/forms/SC1120I.pdf
- **SCDOR conformity statement** (OBBBA / H.3368 pending) —
  https://dor.sc.gov/news/scdor-statement-income-tax-conformity-april-15-filing-deadline-extended-sc-returns
- Statute: **S.C. Code §12-6-545** (ATB election; (G) = entity level), §12-6-2240 et seq.
  (apportionment), §12-6-510 (graduated 0–6%). SC Revenue Rulings **#21-15 / #22-5** (ATB
  governing guidance, cited on the forms). Reusable RS sources from SC1040:
  `SC_ACT63_2025_CONFORMITY` (12/31/2024 conformity), `SC_RR_05_2_DEPR` (§168(k) basis decoupling).

---

## 2. The SC PTET — entity-level Active Trade or Business (ATB) tax

**Statute:** §12-6-545(G) (Act 61 of 2021, effective TY2021). Same §12-6-545 that houses the
individual 3% election (I-335) — applied at the entity level.

**Rate: FLAT 3%** — hardcoded on I-435 L17 ("multiply line 16 by 3%"), NOT a variable rate.
(Contrast GA-700's 5.19%; SC's is a permanent flat 3% on ATB income only.)

**Base: active trade or business income ONLY, SC-apportioned.** Excludes passive investment
income + related expenses, capital gains/losses, IRC §707(c) service payments, and "amounts
reasonably related to personal services" (I-435 instr. p.2; §12-6-545(A)(1)). Apportioned per
§12-6-2240. The ATB active/passive segregation is a **preparer judgment call** → direct-entry
the ATB income (I-435 Col C), compute the tax + flow.

**I-435 structure:** 17 lines, 3 columns — Col A = federal Sch K; Col B = Schedule SC-K; Col C =
SC active trade or business. L14 = total ATB income → SC1065 L2. L15 = ATB already taxed by
another PTE (tiered relief). L16 = taxable ATB. **L17 = L16 × 3% → SC1065 L3.**

**Election:** ANNUAL, NON-BINDING (contrast GA's irrevocable), via a **page-1 checkbox** on the
SC1065 ("Check for Active Trade or Business election"), by the return due date incl. extensions
(§12-6-545(G)(2)). If electing, **also check the box on every SC1065 K-1** issued to partners.

**Owner-side = EXCLUSION, not a credit** (§12-6-545(G)(3)): a qualified owner "shall exclude
active trade or business income from an electing qualified entity provided that the qualified
entity properly filed... and paid the taxes." Mechanically on **I-335 line 6** ("Amounts taxed at
entity level (from SC K-1s)") the owner SUBTRACTS it. Exact pointer: **partner → SC1065 K-1
line 14**; shareholder → SC1120S K-1 line 13. No owner credit; the entity-level 3% is final on
that income.

**Withholding displacement:** entity-taxed ATB income is exempt from the 5% nonresident
withholding — SC1065 **L6 = L1 − L2** removes the entity-taxed ATB before the withholding base.

**Individual I-335 interaction (gotcha to encode):** if the entity does NOT elect, the owner may
still elect the 3% flat on their ATB share via I-335 (vs graduated 0–6%). For TY2025, I-335 has
no benefit if SC taxable income ≤ **$17,830** (top graduated bracket is already 3% there) —
"Do not complete the I-335 if your SC taxable income is ≤ $17,830" (except partners/shareholders
otherwise at a flat 6%). Safe harbor (individual only): if ATB from personal-service entities ≤
$100,000, may treat 50% as not personal-service.

---

## 3. SC1065 face line map (verbatim, Rev. 6/18/25)

```
Page 1:
  [ ] Check for Active Trade or Business election      ← the PTET election checkbox
  L1  Total SC business income                         (← Schedule SC-K line 21)
  L2  Active Trade or Business Income                   (← I-435 line 14)
  L3  ATB Income Tax                                    (← I-435 line 17)  [= L2-taxable × 3%]
  L4  Nonrefundable credits                             (← SC1040TC line 18; direct-entry)
  L5  ATB tax due                                       (L3 − L4)
  L6  SC income taxable to partners                     (L1 − L2)
  L7  Income exempt from withholding                    (residents / I-309 / composite / 501(a))
  L8  Income subject to nonresident withholding         (L6 − L7)
  L9  Nonresident Withholding Tax                       (L8 × 5%)
  L10 Total tax                                         (L5 + L9)
  L11 Tax withheld on the partnership (I-290 / 1099)    (flows IN)
  L12 SC8736 extension payment    L13 Estimated pmts    L15 Total payments
  L16–L18 Refund                  L19–L21 Balance due

Page 2 — Schedule SC-K (col A federal Sch K / B ±SC adj / C after adj / D allocated-SC /
  E allocated-other / F subject to apportionment):
  ... item-by-item federal Sch K → SC adjustments ...
  L16 net business income (before apportionment)
  L17 income subject to apportionment
  L18 total vs SC sales/gross receipts (numerator/denominator)
  L19 apportionment factor (FOUR decimal places)
  L20 = L17 × L19  (apportioned to SC)
  L21 = L16 + L20  (SC-taxable net business income → page 1 L1)
```

---

## 4. SC adjustments, apportionment, depreciation

**Schedule SC-K Column B adjustments (instr. p.4):**
- **§168(k) bonus depreciation add-back** (verbatim): "For the year an asset is placed in
  service, add back the difference between the depreciation taken and the depreciation that would
  have been allowed without bonus depreciation. A subtraction resulting from a higher South
  Carolina basis applies to all remaining years of depreciation." (= the GA-style decoupling; SC
  keeps a separate SC depreciation schedule, RR #05-2.)
- Addition: interest from OTHER states' obligations; expenses related to SC-exempt income.
- Subtraction: US government interest (savings bonds, T-bills).

**Apportionment — 4 methods under §12-6-2240 et seq. (instr. p.3), factor to 4 decimals:**
1. **Sales-only (single sales factor)** — taxpayers dealing in tangible personal property
   (manufacture/sell/rent TPP); SC sales ÷ total sales; destination sourcing.
2. **Gross receipts ratio** — those NOT dealing in TPP (financial + service, installers/repairers,
   contractors); §§12-6-2290, 12-6-2295; SC gross receipts ÷ everywhere.
3. **Special** (§12-6-2310) — railroads, telephone, pipeline, airlines, shipping.
4. **Individualized** (§12-6-2320) — on application.
→ SC is NOT universally single-sales-factor; encode a business-type method selector (methods 1 & 2
  computed; 3 & 4 RED-defer).

**Nonresident partner withholding — 5%** (instr. p.1, verbatim): "Partnerships are required to
withhold 5% of the South Carolina taxable income of partners who are nonresidents." Face L9 = L8 ×
5%. **Exemptions (L7):** SC-resident partners; nonresident partners filing an **I-309 affidavit**;
partners on a **composite return**; partners tax-exempt under **IRC 501(a)**; and ATB income taxed
at the entity level. Each nonresident partner gets a **1099-MISC "SC Only."** Composite: **I-348**
(filing instructions) / **I-338** (affidavit); extension **SC4868**. (I-435 is NOT the withholding
form; withholding is on the SC1065 face. I-290 = inbound real-estate/upstream withholding, L11.)

**IRC conformity: 12/31/2024** (SC1120I "What's New", verbatim) — **did NOT adopt OBBBA** for
TY2025 (OBBBA signed 7/4/2025, after the conformity date). Reuse `SC_ACT63_2025_CONFORMITY`.

**§179 — CONFORMS at the 12/31/2024 level (pre-OBBBA), exact 2025 dollar cap NOT SCDOR-stated.**
§179 is NOT on SC's non-adopted list (unlike §168(k)), so SC allows §179 capped at the pre-OBBBA
regime. The exact figure is ambiguous (see §7 W-flag): Reading A (likely) = 2025-indexed
**$1,250,000 / $3,130,000** (Rev. Proc. 2024-40, flows via the conformed indexing provision);
Reading B (conservative) = 2024 **$1,220,000 / $3,050,000**. SCDOR states no §179 dollar figure —
cite as "IRC §179 as conformed at 12/31/2024; 2025 indexed amounts per Rev. Proc. 2024-40, pending
SCDOR confirmation." Ken (depreciation CPA) to adjudicate.

---

## 5. SC1120S (deferred) — why SC1065 first

SC1120S (Rev. 6/17/25) is a TWO-PART return (Part I income tax + Part II **license fee** =
capital & paid-in surplus × .001 + $15, min $25) and remits nonresident **shareholder**
withholding on a SEPARATE **SC1120S-WH** form, plus a Schedule D Annual Report required of all
corporations, and Schedules E/H-1/H-2/H-3/G. Its ATB lines (L5 ← I-435 L14; L6 ← I-435 L17; L8 SC
net taxable × **5%** general rate; L10 total) mirror SC1065 but sit behind the multi-state
Schedule G reconciliation. **~80% of SC1065 (Schedule SC-K, apportionment, bonus add-back, the
I-435 3% engine) ports to SC1120S**; the S-corp adds only the license-fee module + SC1120S-WH +
Schedule D/G. Author SC1065 first (cleaner, self-contained PTET vehicle), SC1120S as a follow-up.

**Three distinct SC rates to keep straight:** entity ATB = **3%** (I-435); general S-corp SC
income tax = **5%** (SC1120S L9); nonresident PTE withholding = **5%** (SC1065 L9 / SC1120S-WH).
Partnership side has two (3% ATB, 5% withholding); the partnership itself pays NO general income
tax on non-ATB income (that passes to partners).

---

## 6. Reconcile targets (D-1) + tts integration

- tts attaches state returns to the federal 1065 via `state_returns` (GA-700 / GA-600S precedent).
  At the reconcile leg, survey (read-only — parallel-session boundary) whether tts has any SC
  entity compute (almost certainly none). Do NOT edit tts from this session.
- The bonus add-back / §179 delta mirror GA-700 (B): direct-entry the asset-level SC-4562-style
  figures in v1; the engine's `state_*` depreciation fields can auto-populate later.
- Owner-side exclusion (SC1065 K-1 L14 → I-335 L6) is the SC analog of GA's PTEDED/PTEADD — a
  flow assertion, not a compute the entity return owns.

---

## 7. Confidence flags → requires_human_review WALK items (verify before locking)

- **W1. §179 2025 dollar cap AMBIGUOUS.** $1.25M/$3.13M (indexed, likely) vs $1.22M/$3.05M (2024,
  conservative). NOT SCDOR-stated. Ken's depreciation-CPA call. Cite to conformed IRC §179 +
  Rev. Proc. 2024-40, not to SCDOR.
- **W2. H.3368 CONFORMITY LIVE WIRE.** Pending SC bill would conform to OBBBA mid-season → §179
  jumps to $2.5M/$4M and bonus treatment changes. Treat ALL depreciation/§179 logic as
  re-verify-when-H.3368-resolves. (SCDOR flagged this explicitly.)
- **W3. 3% ATB rate + 5% withholding rate** — both primary-verified verbatim (I-435 L17; SC1065
  instr. p.1). Stable for TY2025. Year-key anyway.
- **W4. ATB active/passive segregation** is preparer judgment (what's "reasonably related to
  personal services") — v1 direct-enters the I-435 Col C ATB income; the 3% + flow are computed.
- **W5. Apportionment method selection** by business type (TPP → sales-only; service/financial →
  gross-receipts). v1 computes methods 1 & 2 (selectable); RED-defers special/individualized.

---

## 8. v1 scope — PROPOSED (Ken's walk pending, AskUserQuestion 2026-07-05)

Proposed MAXIMAL v1, mirroring GA-700's shape:
- **A. Entity = SC1065 (partnership) first** (SC1120S deferred; ~80% ports later).
- **B. PTET/I-435 = COMPUTE** the 3% ATB tax (L2→L3) + the owner-exclusion flow (K-1 L14 → I-335
  L6) + the withholding displacement (L6 = L1 − L2); direct-entry the ATB income (Col C, W4).
- **C. Depreciation = COMPUTE** the §168(k) bonus add-back structure (year-1 add-back, remaining-
  life subtraction) + the §179 conformity delta, with the W1 §179 cap flagged (Ken picks the
  reading); direct-entry the asset-level SC-4562 figures (GA-700 (B) precedent).
- **D. Apportionment + withholding = COMPUTE** methods 1 & 2 (business-type selector, 4 decimals)
  + the 5% nonresident withholding with the full exemption set (residents/I-309/composite/501(a)/
  entity-taxed ATB); RED-defer composite (I-348/I-338), special/individualized apportionment;
  direct-entry SC1040TC credits (L4).
