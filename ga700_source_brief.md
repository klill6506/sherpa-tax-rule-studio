# GA Form 700 + PTET (Georgia Partnership Return) — Source Brief (TY2025)

*Prepared 2026-07-05 to kick off the **GA-700 + PTET** authoring campaign (August RS state track, form 4
— after SC1040 ✅, AL Form 40 ✅, NC D-400 ✅). TRANSCRIPTION AID / reconcile map — **NOT a spec and NOT
authorization to seed.** Per D-1, authored FRESH from GA DOR primary sources, each mismatch a logged Ken
adjudication. Constants VERIFIED against the FINAL 2025 GA DOR sources (research agent, 2026-07-05: 2025
Form 700 Rev. 09/11/25; 2025 IT-711 Partnership booklet; HB 149 PTET FAQ; Reg. 560-7-3-.03). §10 flags
the few needing a last look. This is the **1st partnership-entity state return** in RS — GA600S (S-corp,
`load_remaining_1120s.py`) is the closest GA entity precedent; GA Form 500 (individual) also precedes.*

---

## 1. Primary sources (all dor.georgia.gov, TY2025 FINAL)

- **Form 700** (the return, 8 pages) — Rev. **09/11/25** — https://apps.dor.ga.gov/FillableForms/webpdf/examples/2025GA700.pdf
  (landing: dor.georgia.gov/2025-700-partnership-tax-return)
- **IT-711 Partnership Income Tax Booklet** (Form 700 instructions, 24 pp.) — 2025 —
  https://dor.georgia.gov/document/document/2025-it-711-partnership-income-tax-booklet/download
- **HB 149 Pass-Through Entity Tax FAQ** — https://dor.georgia.gov/hb-149-pass-through-entity-tax-faq
- **Income Tax Federal Tax Changes** (conformity) — https://dor.georgia.gov/taxes/tax-rules-and-policies/income-tax-federal-tax-changes
- **Reg. 560-7-3-.03** "Election to Pay Tax at the Pass-Through Entity Level" (via Cornell LII; GA SoS host is JS-only, §10 flag 6)
- Statutory backing: O.C.G.A. **§48-7-21** (PTE tax election), **§48-7-20** (rate), **§48-7-27** (GA adjustments),
  **§48-7-31** (apportionment/allocation), **§48-7-129** (nonresident withholding).

---

## 2. Structure — how Form 700 flows (verbatim; entity return, flows from federal Form 1065)

**KEY: Form 700 starts from FEDERAL partnership income (Schedule 8 ≈ federal Schedule K), applies GA
additions/subtractions (Sch 5/6), apportions by a SINGLE gross-receipts factor (Sch 7), and — only if the
PTET election is made — taxes the GA net income at 5.19% (Sch 1/2). Without the election, Schedules 1 & 3
are left blank (a non-electing partnership is a pass-through; tax is at the partner level).**

```
Sch 8 Total income for GA purposes (≈ federal Sch K): L1 Ordinary income .. L5 Guaranteed payments .. L7 other
      L8 Total federal income → L9 + Additions (Sch 5 L8) → L11 − Subtractions (Sch 6 L5) → L12 → Sch 2 L1
Sch 5 GA ADDITIONS: non-GA muni interest, other-jurisdiction income taxes, intangible expenses, ...,
      L7 OTHER ADDITIONS (← federal bonus depreciation add-back), L8 total → Sch 8 L9
Sch 6 GA SUBTRACTIONS: US-obligation interest, intangible/REIT exceptions,
      L4 OTHER SUBTRACTIONS (← GA depreciation from GA Form 4562), L5 total → Sch 8 L11
Sch 7 APPORTIONMENT (single factor): L1 gross receipts Col A (GA) / Col B (everywhere);
      L2 GA ratio = A ÷ B to SIX DECIMALS → Sch 2 L4
Sch 2 GA NET INCOME: L1 total (Sch 8 L12); L2 allocated everywhere; L3 = L1−L2 (business income);
      L4 GA ratio (Sch 7); L5 = L3×L4 apportioned; L6 allocated to GA; L7 = L5+L6 → Sch 1 L1
Sch 1 GA TAXABLE INCOME + TAX (PTET path only): L1 GA net income; ...; L6 GA taxable income;
      L7 INCOME TAX = 5.19% × L6
Sch 3 TAX DUE / OVERPAYMENT: L1 total tax (Sch 1 L7); L4 withholding credits (G2-A/G2-LP/G2-RP);
      L5 Schedule-10 credits; net due/refund
Sch 4 INCOME TO PARTNERS: per partner — name/ID/profit-loss % / GA source income
Sch 9 GA NOL (80% limit); Sch 10/10B/11 credits (usage / refundable / allocation to owners)
Page 1 header: PTET election checkbox; Composite Return box; nonresident-partner Y/N + count;
      T. Nonresident withholding paid by the partnership
```

---

## 3. Flat / PTET rate (§48-7-20) — TY2025 = **5.19%** ✔ (Form 700 face + IT-711)

IT-711 "What's New" (p.5) verbatim: *"The tax rate for the taxable year beginning on or after January 1,
2025 is 5.19%."* Form 700 Sch 1 L7 hardcodes *"Income Tax (5.19% x Line 6)."* Step-down: 2024 = 5.39%,
**2025 = 5.19%**, 2026 = 4.99% (DOR Important Tax Updates). Year-keyed; ⚠ §10 flag 1 — re-verify each
season. Note: **Reg. 560-7-3-.03 still literally prints "5.75 percent"** (its 2022 text, with a "if
subsequently changed, the applicable statutory rate" saving clause) — the OPERATIVE 2025 rate is 5.19%;
the 5.75% survives only in the UET prior-year safe-harbor computation (§10 flag 5).

---

## 4. THE PTET ELECTION (HB 149 / O.C.G.A. §48-7-21; Reg. 560-7-3-.03) — the headline feature

**Election:** a partnership may **annually make an IRREVOCABLE election** to pay income tax at the entity
level. Made by **checking the box "Partnership elects to pay the tax at the entity level" on Form 700
page 1** by the (extended) due date. TY2023+, **ALL partnerships are eligible** regardless of ownership.

**Base — a SINGLE entity-level number (NOT a resident/nonresident split — §10 flag 3):** federal taxable
income *including separately-stated items* (charitable, §179, etc.), **limited to what a C-corporation
would be allowed**; NO §743(b), NO self-employment / SE-health / Keogh / SEP deductions; then the
**O.C.G.A. §48-7-27 GA adjustments** (Sch 5/6); then **apportioned/allocated under §48-7-31** (single
gross-receipts factor) → "income taxed at the entity level." NO §48-7-26 exemptions / standard deduction /
natural-person deductions (e.g. retirement exclusion).

**Tax = base × 5.19%** (Reg. says 5.75% "or the applicable statutory rate" → 5.19% for 2025).

**Owner treatment:** electing owners **exclude** the entity-taxed income — on **Form 500 Schedule 1**:
share of income taxed at entity level = **subtraction, Line 12, "PTEDED"**; share of loss = **addition,
Line 5, "PTEADD."** **NO owner credit** for GA tax paid at the entity level. Election is **binding on all
partners incl. nonresidents**, and **displaces nonresident withholding / composite** (no IT-CR when
elected). A nonresident whose ONLY GA income is the entity-taxed income need not file a GA return.

**Limitations:** tax attributes (credits, NOLs) **stay with the entity**; the entity MAY make a separate
irrevocable election to pass through credits generated that year **except** Qualified Education Expense /
Qualified Education Donation / Qualified Rural Hospital Expense. No deduction for income-based taxes.
Estimates on **Form 602-ES** (C-corp-style), required if net income > **$25,000**; owner estimates can't
transfer to the entity. Guaranteed-payment-to-retiree special rule (Reg. .03(8)): subtract before
apportioning, no PTEDED/PTEADD for that share. **When the election is NOT made, leave Form 700 Schedules
1 & 3 BLANK** (else a false balance-due is generated).

---

## 5. Depreciation / conformity — GA decouples from §168(k), keeps its own §179 (Ken's specialty)

**GA does NOT conform to IRC §168(k) bonus or to OBBBA.** Mechanic (DOR Federal Tax Changes, verbatim):
*"Federal depreciation should be added back to Georgia income by entering it on the other addition line…
Depreciation must then be computed for Georgia purposes on Georgia Form 4562… Georgia depreciation should
be entered on the other subtraction line."* On Form 700: **federal depreciation add-back → Sch 5 L7 (other
additions); GA depreciation → Sch 6 L4 (other subtractions).** Net adjustment = federal depr − GA depr
(the bonus/§179 delta). Later asset sale → GA gain/loss differs (basis difference).

**GA §179 = $1,050,000 limit / $2,620,000 phaseout** (DOR's last-published figure, under a "2021" heading;
GA did NOT adopt the OBBBA $2,500,000/$4,000,000 — matches CLAUDE.md verified GA rules). ⚠ §10 flag 4 —
last *published* figure, re-verify with the 2025 conformity bill.

**IRC conformity date = Jan 1, 2024** (HB 1162; DOR has NOT posted a 2025 conformity bill yet). ⚠ §10 flag
1 — GA passes an annual conformity bill each spring; re-verify before locking. Other GA decoupling: no
§199A QBI; **§163(j) as it existed PRE-TCJA** (30% limit; IT-711 p.9); §174 R&E still currently deductible
(GA didn't adopt TCJA 5-yr amortization).

---

## 6. Apportionment — SINGLE gross-receipts factor (Sch 7), since 2008

IT-711 (pp.11-12) verbatim: *"the Georgia apportionment ratio shall be computed by applying only the gross
receipts factor."* **GA ratio = GA gross receipts ÷ everywhere gross receipts, to SIX decimals, do not
round** (Sch 7 → Sch 2 L4). Market-based/customer-destination sourcing (§560-7-7-.03). Investment
intangibles + pure-investment real-estate rentals are **allocated, not apportioned**.

---

## 7. Partner shares (Schedule 4) + nonresident withholding (4%)

**Schedule 4 (Income to Partners):** per partner — name/address/ID, **profit-loss-sharing %**, **GA source
income**. IT-711 p.11: a **resident partner reports his FULL share**; a **nonresident reports only his
GA-apportioned + GA-allocated share**. GA-source ≠ total because guaranteed payments aren't profit-%-based.
**Worked example (IT-711 p.13, a precise test oracle):** 2 partners (25% GA-resident / 75% nonresident),
$100 ordinary (Sch 8 L1) + $50 guaranteed payments (Sch 8 L5), GA ratio 50%, total GA-purpose income $150
→ **resident reports $35** ($10 full GP + 25%×$100); **nonresident reports $58** ($40 GP × 50% + $100×75%×50%).

**Nonresident withholding (§48-7-129):** *"The withholding tax rate is 4%"* on each nonresident partner's
GA-source income; **NO withholding if the partner's GA share < $1,000**; remitted via **G-2-A** (credited
Sch 3 L4). Alternative: **composite return on Form IT-CR** (check the box, no permission needed).
NRW-Exemption (Reg. 560-7-8-.34). **PTET election displaces all of this** (the entity tax covers nonresidents).

---

## 8. Filing / entity notes

- **Who files:** partnerships / LLCs taxed as partnerships with GA business, property, GA-domiciled
  members, or GA-source income. **Due 15th day of 3rd month (March 15 calendar-year).** Federal 7004 → GA
  6-month extension (attach; check box); extension to FILE not PAY (IT-560C).
- **Partnerships are NOT subject to GA net worth tax** (contrast GA600S Schedule 3 — omit it for Form 700).
- **S-corp PTET is a DIFFERENT form (Form 600S, already in RS as GA600S)** — same 5.19%, same PTEDED/PTEADD.
- **E-file** required whenever the federal counterpart must be e-filed, and always if a Series-100 credit is claimed.

---

## 9. Federal handoff points

1. **Sch 8 L1-L8** = federal Form 1065 Schedule K items (ordinary income, rental, portfolio, guaranteed
   payments, §1231, other) → total federal income.
2. **Depreciation:** federal depreciation (incl. §168(k) bonus) add-back → Sch 5 L7; GA Form 4562
   recompute (no bonus, GA §179 limits) → Sch 6 L4.
3. **Partner profit-loss %** = the ending % from each federal K-1 (Sch 4).
4. **PTET owner side** lands on the partner's **Form 500 Schedule 1** (PTEDED L12 / PTEADD L5).

---

## 10. Confidence flags → requires_human_review WALK items (verify before locking)

1. **IRC conformity date = Jan 1, 2024** — DOR has not posted a 2025 conformity bill; GA passes one each
   spring. Load-bearing for depreciation + §179. Re-verify against the 2025 GA conformity bill before locking.
2. **Flat/PTET rate 5.19%** — DOR-primary (Form 700 face + IT-711), solid; year-keyed, re-verify each season
   (2026 → 4.99%).
3. **PTET base is ENTITY-LEVEL** (federal taxable income → §48-7-27 → §48-7-31 apportionment → 5.19%), NOT a
   resident/nonresident split. Encode accordingly.
4. **§179 $1,050,000 / $2,620,000** — GA's last *published* figure (2021 heading); GA did NOT adopt OBBBA.
   Matches CLAUDE.md. Re-verify with flag 1 (the 2025 conformity bill).
5. **Reg. still prints 5.75%** — stale text; operative 2025 rate is 5.19%. But the UET prior-year
   safe-harbor computation literally uses 5.75% (only relevant if UET penalty is modeled — RED-defer).
6. **Reg. 560-7-3-.03 text from Cornell LII** (GA SoS host JS-only) — cross-checks vs DOR FAQ + IT-711;
   low risk. Pull from rules.sos.ga.gov in a browser for a belt-and-suspenders cite if needed.

---

## 11. Proposed v1 scope (COMPUTES / DIRECT-ENTRY / RED-DEFER framework) — FOR KEN'S WALK

**COMPUTES (proposed):** the base Form 700 (Sch 8 → 5/6 → 2 → 1); the single gross-receipts apportionment
(Sch 7, 6 decimals); **the PTET election path** — entity-level GA taxable income × 5.19% (Sch 1 L7), the
PTEDED/PTEADD owner-side documentation; **Schedule 4 partner allocation** (resident full / nonresident
GA-apportioned + allocated, guaranteed-payment handling); **the 4% nonresident withholding** (<$1,000
exemption); the §179 GA-limit difference.

**DIRECT-ENTRY (line exists, diagnostic prompts):** the GA Form 4562 depreciation figures (federal-depr
add-back Sch 5 L7 + GA-depr subtraction Sch 6 L4 — asset-level, needs the GA-4562 recompute); Schedule 10
credits; niche Sch 5/6 items (intangible/REIT add-backs, IT-Addback/IT-REIT); allocated-everywhere income
(Sch 2 L2/L6).

**RED-DEFER (each its own "prepare manually" RED):** GA NOL (Schedule 9, 80% limit); composite return
(Form IT-CR); the UET estimated-tax underpayment penalty (Form 600UET, incl. the 5.75% prior-year quirk);
credit pass-through election + allocation (Sch 11).

**Open decisions for the walk (4, AskUserQuestion):**
- **(A) PTET election** — COMPUTE the full entity-level PTET path (5.19% tax + PTEDED/PTEADD owner
  mechanics) [the headline], or base-return-only with PTET as a flagged/direct-entry?
- **(B) Depreciation add-back** — COMPUTE the §179 GA-limit difference + model the Sch 5 L7 / Sch 6 L4
  add-back/subtract structure, DIRECT-ENTRY the asset-level GA-Form-4562 depreciation delta; OR full
  direct-entry (both figures preparer-supplied, GA-500 W1 pattern)?
- **(C) Partner allocation + nonresident withholding** — COMPUTE Schedule 4 (resident full / nonresident
  GA-source) + the 4% withholding (<$1,000 exemption); OR direct-entry the partner GA-source figures?
- **(D) Credits & niche** — DIRECT-ENTRY Schedule 10 credits + intangible/REIT add-backs; RED-defer GA NOL
  (Sch 9) / composite IT-CR / UET penalty / credit pass-through (Sch 11) — confirm the split.

Plus bless the §10 verify flags (conformity Jan 1 2024 re-verify; 5.19% year-keyed; entity-level PTET base;
§179 figures; reg-5.75%-vs-operative-5.19%).
