# SC1040 (South Carolina Individual Income Tax) — Source Brief (TY2025)

*Prepared 2026-07-04 to kick off the **SC1040** authoring campaign (August RS state track,
"CC drafts, Ken walks — GA-500 pattern"). This is a TRANSCRIPTION AID / reconcile map — **NOT a
spec and NOT authorization to seed.** Per D-1, the spec is authored FRESH from SC DOR primary
sources, then reconciled against the existing tts state-return compute, and every mismatch is a
logged Ken adjudication. All constants below were VERIFIED against the final 2025 SC DOR PDFs (a
research agent read them 2026-07-04); the confidence flags in §7 mark the handful that need a
last look before locking. This is the **2nd state individual spec** (GA Form 500 is the first;
`load_ga500_form_500.py` is the structural precedent).*

---

## 1. Primary sources (all dor.sc.gov, TY2025 final)

- **SC1040 form** — "2025 Individual Income Tax Return," **Rev. 4/21/25**, form ID 3075 —
  https://dor.sc.gov/sites/dor/files/forms/SC1040_2025.pdf
- **SC1040 Instructions** — "2025 Individual Income Tax Instructions" (~Aug 2025 build, no printed
  rev date) — https://dor.sc.gov/sites/dor/files/forms/SC1040Instr_2025.pdf
- **SC1040TT** — "2025 South Carolina Individual Income Tax Tables" + Rate Schedule, **Rev.
  6/17/25** — https://dor.sc.gov/sites/dor/files/forms/SC1040TT_2025.pdf
- Statute for the bracket thresholds: **SC Code §12-6-510** (annually inflation-indexed) — NOT
  fetched; see §7 flag 1.

---

## 2. Structure — how SC1040 flows (verbatim labels from the Rev. 4/21/25 form)

**Starts from FEDERAL TAXABLE INCOME** (not AGI — contrast GA-500 which starts from federal AGI).

```
L1  Federal taxable income (← federal 1040 line 15; DOR prints only "your federal form")
      Additions a–e  → L2 total additions
L3  = L1 + L2
      Subtractions f–w → L4 total subtractions
L5  SOUTH CAROLINA INCOME SUBJECT TO TAX = L3 − L4 (not < 0)
      [Nonresident/part-year: L5 ← Schedule NR line 48, bypassing L1–L4]
L6  TAX (from SC1040TT / rate schedule)
L7  Tax on Lump-Sum Distribution (SC4972)         L8  Tax on Active Trade/Business Income (I-335)
L9  Tax on excess Catastrophe Savings withdrawals L10 TOTAL SC TAX = 6+7+8+9
L11 Child & Dependent Care  L12 Two Wage Earner  L13 Other nonref. (SC1040TC)  L14 total  L15 = 10−14
L16 SC withholding  L17 est. pmts  L18 extension  L19 nonres. real-estate (I-290)  L20 other wh (1099)
L21 Tuition tax credit (I-319, refundable)  L22a-d refundable credits  L22 total  L23 TOTAL PAYMENTS
L24 overpayment  L25 amount due  L26 use tax  L27 applied to 2026 est  L28 check-offs (I-330)
L29 total(26-28)  L30 REFUND  L31 tax due  L32 late penalties+interest  L33 SC2210  L34 BALANCE DUE
```

**Federal handoffs (attaches to the child 1040 in tts via `state_returns`, the GA-600S/GA-500
precedent):** L1 ← federal taxable income (1040 L15); line-a addback ← federal Sch A SALT; line-i
← federal net capital gain (federal holding period); L11 ← federal Form 2441 expense; line-r ←
negative federal taxable income (entered positive).

---

## 3. TY2025 rate schedule — VERIFIED (was the top-priority item)

**Top rate = 6%** for 2025 (down from 6.4% in 2024, via SC's statutory reduction trigger). Confirmed
in SC1040TT (Rev. 6/17/25). Three brackets, **same for all filing statuses**:

| Bracket | Rate |
|---|---|
| $0 – $3,560 | **0%** |
| $3,561 – $17,830 | **3%** |
| over $17,830 | **6%** |

- For taxable income **≥ $100,000** the rate schedule is: `tax = 6% × L5 − $642`. The **$642**
  constant is verbatim from SC1040TT and internally consistent with the 0/3/6% thresholds.
- For **< $100,000**, SC1040TT is a bracketed lookup table (use the table, not the formula).
- ⚠ The **$3,560 / $17,830** dollar thresholds are corroborated by the SC1040TT breakpoints but are
  NOT printed as round numbers in the DOR booklet — §7 flag 1 (verify vs SC Code §12-6-510).

**Year-keyed constant (mirror GA's `GA_TAX_RATE` pattern):**
`SC_TOP_RATE = {2025: "0.06"}` · `SC_RATE_SCHED_SUBTRACT = {2025: 642}` ·
`SC_BRACKET_0_TOP = {2025: 3560}` · `SC_BRACKET_6_FLOOR = {2025: 17830}` (all re-verify each year).

---

## 4. Additions (a–e) and the key subtractions (f–w)

**Additions to federal taxable income:**
- a — state tax addback if itemized federally (federal SALT cap referenced as **$40,000 / $20,000
  MFS** in the 2025 booklet)
- b — out-of-state losses · c — NG/Reserve income expenses · d — non-SC muni bond interest
- **e — other additions — INCLUDES the IRC §168(k) bonus-depreciation add-back** (SC does not
  conform to federal bonus; taxpayer adds back federal-minus-nonbonus depreciation). Also SC-larger
  federal NOL and accounting-method items. **← the depreciation/conformity item, Ken's specialty
  (the GA-500 W1 analog).**

**Subtractions — verified amounts:**
| Line | Item | 2025 rule |
|---|---|---|
| i | **44% net capital gain deduction** | long-term gain reduced by **44%** (CONFIRMED 2025) |
| o | **Social Security / RR retirement** | **fully exempt** (subtract amount taxed federally) |
| p-1/2/3 | **Retirement deduction** | under 65 up to **$3,000**; age 65+ up to **$10,000** (per taxpayer, own qualified retirement income) |
| p-4/5/6 | **Military retirement** | **100%**, no cap (since TY2022); reduces p-1/2 and q-1/2 |
| q-1/2 | **Age 65+ deduction** | **$15,000** per taxpayer 65+, any SC income; reduced by p-1/2 and p-4/5 already claimed |
| t | **Dependents under age 6** | **$4,930 × #under-6** (stacks on top of line w for the same child) |
| w | **SC Dependent Exemption** | **$4,930 × # federal dependents** (children + qualifying relatives) |
| f | state tax refund | · g total-&-permanent-disability retirement · h out-of-state income · j volunteer $6,000 · k Future Scholar 529 · l Active Trade/Business (I-335, 3% election) · m US-obligation interest · s subsistence $16/workday · u consumer protection · v other (adoption $2,000, ABLE, etc.) |

---

## 5. Credits

- **L11 Child & Dependent Care** — **7%** of the federal 2441 expense; **max $210 / $420** (1 / 2+
  dependents); not MFS.
- **L12 Two Wage Earner** — MFJ only; **0.7% × lesser($50,000, lower-earner SC earned income)**;
  **max $350**.
- **L13 Other nonrefundable** → **SC1040TC** (attach; all other business/misc credits computed there).
- **L21 Tuition Tax Credit (I-319, REFUNDABLE)** — **50% of tuition, max $1,500**, 2-/4-yr SC schools,
  ≤4 consecutive years. ⚠ cap from RR24-3 / DOR web, not the 2025 instructions — §7 flag 3.
- **L22a-d refundable** — Anhydrous Ammonia (I-333), Milk (I-334), Classroom Teacher (I-360),
  Parental Refundable (I-361).

---

## 6. Residency

- Face checkbox "Part-Year/Nonresident … filing an SC Schedule NR."
- PY/NR filers complete **Schedule NR** and carry **Sch NR line 48 → SC1040 line 5** (bypassing
  L1–L4). Line 1 instruction: "STOP! nonresident/part-year → complete Schedule NR, go to line 5."
- Schedule NR yields a proration % used for some credits. Separate form (`SchNRInst_2025.pdf`), not
  transcribed here.

---

## 7. Confidence flags → requires_human_review WALK items (verify before locking)

1. **Bracket thresholds $3,560 / $17,830** — derived + cross-checked against primary SC1040TT
   breakpoints and the $642 constant, but the exact figures came from a third-party site, not a DOR
   PDF. **Verify vs SC Code §12-6-510** (inflation-indexed). The 6% top rate + $642 ARE primary-verified.
2. **Federal line for L1** — DOR says "your federal form," doesn't print "line 15." 1040 L15 is the
   2025 federal layout (map, don't cite to DOR).
3. **Tuition credit cap ($1,500 / 50% / 4 yr, refundable)** — from RR24-3 + DOR web page, NOT the
   2025 SC1040 instructions (which route to I-319); the 2025 I-319 PDF wasn't fetched. Re-verify on
   the final **I-319_2025** if the spec computes it.
4. **Dependent exemption phase-out** — 2025 worksheet is a flat multiply, no phase-out shown. "None
   found," not "confirmed none."
5. **Instructions rev date** — SC1040Instr_2025 carries no printed rev date (~Aug 2025 build).

---

## 8. Reconcile targets (D-1) + tts integration

- tts attaches state returns to the child 1040 via `TaxReturn.federal_return` / `state_returns`
  (the GA-600S + GA-500 precedent). Confirm whether tts already has any SC compute (likely none —
  survey at the reconcile leg, read-only; do NOT edit — parallel session boundary).
- The depreciation add-back (line e) mirrors GA-500's W1: the engine's `Asset.state_*` fields can
  auto-populate the SC-vs-federal depreciation difference in a later integration; v1 likely
  preparer direct-entry (Ken's call).

---

## 9. Proposed v1 scope (mirrors the GA-500 COMPUTES / DIRECT-ENTRY / RED-DEFER framework) — FOR KEN'S WALK

**COMPUTES (proposed):** the resident main form L1→L34; the 3-bracket tax (L6, table + ≥$100k
schedule); the **retirement / military / age-65 deduction stack** (p/q with the interacting
reductions — the SC center of gravity, like GA's RIE); the 44% capital-gain deduction (i); SS
subtraction (o); dependent exemption (w) + under-6 (t); child-care (L11) & two-wage-earner (L12)
credits; withholding/payments → refund/balance.

**DIRECT-ENTRY (line exists, diagnostic prompts, preparer keys the SC-vs-federal figure):** line-e
§168(k) depreciation add-back (W-dep, engine auto-populates later); other a–e / f–w niche
add/subtracts; SC1040TC other credits (L13); tuition credit inputs (L21).

**RED-DEFER (each its own "prepare manually" RED — no silent gap):** Schedule NR part-year/
nonresident (if not in v1 — see decision A); Active Trade/Business 3% election (I-335, L8/line-l);
lump-sum (SC4972, L7) + catastrophe-savings (L9); SC2210 underpayment (L33).

**Open decisions for the walk:** (A) residency scope — resident-only v1 with NR RED-deferred, or
full resident + Schedule NR like GA-500; (B) the line-e depreciation add-back — preparer direct-
entry (GA-500 W1 precedent) or computed; (C) the p/q retirement-deduction stack depth; (D) I-335
active-trade-business + special taxes (SC4972 / catastrophe) — RED-defer or compute. Plus bless the
§7 verify-before-lock flags.
