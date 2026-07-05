# Form 1041 Module (S-11 / WO-09) — Source Brief

*Greenfield RS-first authoring brief for the federal 1041 fiduciary module + GA Form 501.
Opened 2026-07-05. Front-door step: GAP-CHECKED → research-verified (this file) → Gate-1 scope walk → author.*

**Every TY2025 figure below was verified VERBATIM against FINAL primary sources by three research
passes (never memory), per the Authoritative-Source Rule.** Extracted PDF text dumps live in
`scratchpad/` (`f1041`, `f1041sk1`, `i1041`, `i1041sk1`, `k1instr.txt`, `char.txt`, `grantor.txt`)
for seeding verbatim excerpts during authoring.

---

## Authoritative sources (all FINAL 2025)

| Source | Scope | Rev/date |
|---|---|---|
| **Form 1041 (2025)**, Cat. 11370H | Page-1 income/deductions, Schedule B (p.2), Schedule G (p.2) | Created 10/28/25 |
| **i1041 (2025)**, Cat. 11372D | Instructions for 1041 + Sch A/B/G/J/K-1 | Mar 5, 2026 |
| **Schedule K-1 (Form 1041) 2025**, Cat. 11380D | Beneficiary boxes 1–14 + codes | Created 5/2/25 |
| **i1041 Sch K-1 (2025)**, Cat. 11374Z | Beneficiary K-1 instructions | Mar 13, 2025 |
| **Rev. Proc. 2024-40** | TY2025 inflation figures (§1(e) brackets, cap-gain, §642(b)(2)(C)) | governs TY2025 |
| **IRC §643 / §651 / §661 / §662 / §663 / §642(b) / §1(e) / §1411** | DNI, distribution deductions, tiers, exemptions, rate, NIIT | Cornell LII |
| **Reg. §1.643(a)-3** | Capital gains in DNI (three circumstances) | Cornell LII |
| **GA Form 501 (2025)** + **2025 501/501X Fiduciary Instructions booklet** | GA fiduciary return | Rev. 07/09/25 |
| **O.C.G.A. §48-7-27 / §48-7-129 / §48-7-114** | GA fiduciary adjustments, NR withholding, estimated tax | booklet-cited |

> **NOT a source for TY2025:** Rev. Proc. **2025-32** is the **TY2026** procedure (verified). It does
> NOT alter any 2025 estate/trust figure; the final i1041 re-confirms all 2025 values. (For the eventual
> TY2026 re-cut: 2025-32 gives estate/trust breakpoints $3,300/$11,700/$16,000, AMT exemption $31,400.)

---

## Verified TY2025 constants (locked)

**§1(e) estate & trust rate schedule** (Rev. Proc. 2024-40 Table 5; re-confirmed i1041 "2025 Tax Rate Schedule"):
| Taxable income | Tax |
|---|---|
| ≤ $3,150 | 10% |
| $3,150–$11,450 | $315 + 24% of excess over $3,150 |
| $11,450–$15,650 | $2,307 + 35% of excess over $11,450 |
| > $15,650 | $3,777 + 37% of excess over $15,650 |

**§642(b) exemptions:** decedent's estate **$600** · simple trust **$300** · complex trust **$100** ·
qualified disability trust **$5,100** (Rev. Proc. 2024-40 §2.35; not subject to phaseout).

**Capital-gains breakpoints (estates & trusts):** 0% ≤ **$3,250**; 15% to **$15,900**; 20% over $15,900
(Rev. Proc. 2024-40 §2.03; re-confirmed i1041 What's New).

**§1411 NIIT threshold (trusts/estates):** **$15,650** (= top §1(e) bracket start); 3.8% on the lesser of
undistributed NII or (AGI − $15,650). Form 8960 line 21 → Schedule G Part I line 5.

**GA fiduciary rate:** flat **5.19%** (H.B. 1437 accelerated schedule; booklet What's New + Line 8).
**GA exemptions:** trust **$1,350** / estate **$2,700**. **GA conformity:** IRC as enacted **on/before Jan 1, 2025**;
**OBBBA NOT adopted** for TY2025. **GA NR member withholding (§48-7-129):** 4%, $1,000 de minimis — owner-level only.

---

## Gap map — required set (BUILD_ORDER S-11), all 404 GAP

| # | Surface | Proposed RS form key | Content |
|---|---|---|---|
| 1 | **Spine** | `1041` | Page-1 income (L1–9) + deductions (L10–23) + total tax (L24); §642(b) exemption; §67(e) fee-allocation cue on L12/14/15a; QBI L20; OBBBA §1062 L25b |
| 2 | **DNI / IDD / Sch B** | `1041` (page-2 Sch B) | §643(a) 7-modification DNI; Sch B L1–15 smaller-of DNI limitation → page-1 L18 |
| 3 | **Schedule G** | `1041` (page-2 Sch G) | Tax on L1a (rate sched / Sch D wksht / Sch J); ESBT L4; NIIT L5 (8960); credits; total → L24 |
| 4 | **K-1 (1041)** | `SCHEDULE_K1_1041` | Beneficiary boxes 1–14 + full codes (9/11/12/13/14); character retention; tier inclusion |
| 5 | **GA Form 501** | `GA501` | Federal ATI start → Sch 2 adj → Sch 3 beneficiary subtraction (L4) → 5.19% → Sch 4 NR allocation → Sch 5/6 credits |
| 6 | **Schedule I (AMT)** | — | **RED-defer diagnostic only** — ruled **D-2** (2026-07-04). Do NOT author the compute. |

**Proposed form-key consolidation:** the federal 1041 is one physical form; page-1 + Schedule B + Schedule G
are tightly coupled (L18 IDD←Sch B L15; L24 tax←Sch G L9). Propose modeling them as **one `1041` form**
(spine+Sch B+Sch G together), plus separate **`SCHEDULE_K1_1041`** and **`GA501`** — mirroring how the
1065 core kept the coupled page-1+distribution spine together while K-1 was its own form.

---

## Verified mechanics (authoring reference)

### DNI — §643(a) modifications (start from taxable income):
(1) add back §651/§661 distribution deduction; (2) add back §642(b) exemption; (3) exclude capital
gains allocated to corpus & not distributed/set-aside (the default — see Reg. §1.643(a)-3 for inclusion);
(4) simple-trust extraordinary/stock dividends allocable to corpus excluded; (5) **include** tax-exempt
interest, reduced by §265-disallowed expenses + §642(c) charitable portion; (6) foreign-trust income; (7) anti-abuse.

### Schedule B (2025 verbatim, L1–15): DNI on **L7** = combine L1–6. IDD on **L15** = smaller of
L13 (distributions net of tax-exempt) or L14 (DNI net of adjusted tax-exempt interest) → page-1 L18.

### Distribution machinery:
- **§651 simple** = income required to be distributed (L9), capped at DNI.
- **§661 complex/estate** = required (L9, §661(a)(1)) + other paid/credited/required (L10, §661(a)(2)), capped at DNI.
- **Tiers (§662):** L9 = first-tier (DNI applied first); L10 = second-tier (remaining DNI). Beneficiary
  includes proportionate DNI share (Reg. §§1.652(c)-4, 1.662(c)-4).
- **Separate share (§663(c)):** substantially-separate shares treated as separate trusts *for DNI allocation only*.
- **65-day election (§663(b)):** complex trust/estate may treat distributions within 65 days after year-end
  as made on the last day — checkbox at **Question 6**; irrevocable.
- **Character (i1041 p.44):** each beneficiary's income has the same class-proportion as DNI (½ interest /
  ½ dividends if DNI is such). Directly-attributable deductions first; indirect allocated with a reasonable
  portion to tax-exempt; charitable ratably apportioned.

### Capital gains IN DNI — Reg. §1.643(a)-3(b), the three circumstances (gains included to the extent,
per governing instrument/local law or reasonable discretion, they are): (1) allocated to income;
(2) allocated to corpus but **consistently treated** as part of a distribution; (3) allocated to corpus but
**actually distributed** or used in determining the distribution. Sch B L3 = gains attributable to income.

### K-1 (Form 1041) 2025 boxes (verbatim): 1 interest · 2a/2b ord/qual div · 3 net ST cap gain ·
4a/4b/4c LT/28%/unrecap-1250 · 5 other portfolio & nonbusiness · 6 ord business · 7 net rental RE · 8 other
rental · **9** directly apportioned deductions (A depr/B depl/C amort) · 10 estate tax deduction ·
**11** final-year deductions (A §67(e) excess/B non-misc itemized/C ST cap-loss CO/D LT cap-loss CO/E NOL/F ATNOL) ·
**12** AMT items (A–J) · **13** credits (A–T, ZZ) · **14** other info (A tax-exempt int · E net investment income ·
**H §1411 NIIT adj → 8960 L7** · **I §199A info** · … ZZ). Grantor trusts do NOT use the K-1 (grantor letter instead).

### Entity-type special computations:
- **ESBT (S portion only):** taxed separately at the highest trust rate via the **ESBT Tax Worksheet** →
  Sch G Part I **L4**. Page-3 Q14/Q15 ESBT-only.
- **Grantor trust:** income to grantor; entity info only, dollars on an attachment (grantor letter), NOT a K-1.
- **Pooled income fund:** files 1041 + Form 5227; does NOT complete Schedule B.
- **Bankruptcy estate (ch. 7/11):** individual-style computation, attach Form 1040; files if gross income ≥ $15,750.
- **§645 election** (G(1)): QRT treated as part of the estate.

### OBBBA (P.L. 119-21) touchpoints on the 2025 return (all verified):
- **New §1062** — qualified farmland sold to qualified farmers: elect 4 annual installments via **new Form 1062**
  (page-1 L25b; Sch G Part II L18c). Low frequency.
- **§174A** domestic research immediate expensing (post-12/31/2024) — affects a trust carrying on a business.
- **SALT worksheet** revision (AGI > $500k).
- **No change** to the §643/651/661/662/663 DNI-IDD machinery, the rate schedule, exemptions, cap-gain
  breakpoints, NIIT threshold, or K-1 boxes for TY2025.

### GA Form 501 mechanics:
- **Base = federal 1041 Adjusted Total Income (line 17), PRE-IDD** (501 L1). GA removes the beneficiary
  share separately at **L4** (Schedule 3 detail) — do NOT double-count the federal distribution deduction.
- Flow: L1 fed ATI → L2 Sch 2 net adj → L4 beneficiary share (Sch 3) → L6 exemption ($1,350/$2,700) →
  L7c net taxable → **L8 × 5.19%** → L9 credits (Sch 5/5B/6).
- **Sch 2 adjustments:** non-GA muni interest (add), US-obligation interest (subtract). **No §168(k)/§179 line** —
  depreciation conformity rides generic Sch 2 "Other" (add L5 / sub L10) under **§48-7-27**; cite the statute + DOR conformity page, not a 501 line.
- **Multi-state = Schedule 4 allocation** (Total vs GA-source columns, ratio L9), NOT formulary apportionment.
- **No separate GA K-1** — beneficiary detail on Schedule 3; credit allocation on Schedule 6; federal K-1 attached.
- **§48-7-129 4% NR withholding** does NOT reach trust→beneficiary (owner-level only); surfaces on 501 **L11b**
  as a credit when the trust is itself a NR member of a PTE or sells GA realty (G2-RP). **PTET N/A** at fiduciary level.

---

## Open flags carried into authoring
- **[year-keyed]** All figures TY2025; re-verify at TY2026 (OBBBA §67/§68 changes bite for years after 12/31/2025;
  the 2026 breakpoints are already known — see 2025-32 note above).
- **§1062 / Form 1062** face line-numbering (L25b / Sch G 18c) confirmed on the form; the installment math is
  low-frequency — propose structure + flag, not full compute (Ken call, low priority).
- **GA general filing threshold** for ordinary trusts/estates not stated in the 2025 booklet (only bankruptcy
  estate $13,850) — cite §48-7-24 / the estimated-tax test, not a booklet page.
- **ESBT Tax Worksheet** (Sch G L4) — full separate-rate compute vs diagnostic is a Gate-1 decision (see scope walk).

---

## Gate-1 scope — LOCKED 2026-07-05 (DECISIONS D-10)
1. **Entity types:** COMPUTE core 4 (estate/simple/complex/QDisT) + **ESBT** (separate-rate wksht → Sch G L4);
   grantor = structure + grantor-letter (no K-1); **PIF → routed to the Form 5227 leg**; bankruptcy = RED-defer diag.
2. **Distribution engine = FULL:** §662 tiers + §663(c) separate-share + §663(b) 65-day + proportional character retention.
3. **Cap-gains-in-DNI = direct-entry** Sch B L3 + the three-circumstance §1.643(a)-3(b) diagnostic (default corpus-excluded).
4. **GA 501 = resident-only v1** — full-year resident (fed ATI → 5.19% → $1,350/$2,700 exemptions → Sch 5/6 credits);
   RED-defer Schedule 4 NR allocation + §168(k)/§179 conformity add-backs.

**Pre-decided:** Sch I AMT = RED-defer (D-2); K-1 full verbatim code transcription (1065-K-1 precedent); form keys
`1041` (spine+SchB+SchG) + `SCHEDULE_K1_1041` + `GA501`; OBBBA §1062 = structure + flag (low frequency).

**Spun off — [WO-10] Form 5227** (PIF + CRT/CRAT/CRUT + CLT, §664(b) four-tier) = its own dedicated leg with its
own research pass + source brief, after the 1041 core.

## Authoring legs (this order, RS-first)
- **(a) `1041`** — spine (page-1 L1–24) + Schedule B (DNI/IDD, full §662/§663 engine) + Schedule G (tax, ESBT L4, NIIT L5). ◀ DRAFTING
- **(b) `SCHEDULE_K1_1041`** — beneficiary boxes 1–14 + full verbatim codes; character/tier pass-through.
- **(c) `GA501`** — resident fiduciary return (fed ATI → 5.19%).
Each: author `READY_TO_SEED=False` → SQLite-validate (CharField caps ≤ 20) → Ken review walk → seed → export = 200.
