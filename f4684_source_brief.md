# Source Brief — Form 4684, Casualties and Thefts (TY2025)

**WO-16 · SPINE S-16 (3rd item after 8990 + Schedule H) · greenfield RS-first**
Research pass 2026-07-05, verbatim vs FINAL 2025 IRS sources. Nothing carried [UNVERIFIED] except the noted window.

---

## Sources (all FINAL, posted)

| source_code | title | citation |
|---|---|---|
| `IRS_2025_F4684` | 2025 Form 4684 — Casualties and Thefts | Form 4684 (2025), Cat. No. 12997O, **Created 9/26/25**, Attach. Seq. No. 26 |
| `IRS_2025_I4684` | 2025 Instructions for Form 4684 | Instructions for Form 4684 (2025), updated 30-Apr-2026 |
| `IRS_PUB547_2025` | Pub. 547 — Casualties, Disasters, and Thefts (2025) | IRS Pub. 547 (2025) |
| `IRC_165` | IRC §165 casualty/theft losses — §165(c)/(h)/(i) | 26 U.S.C. §165(c),(h)(1)-(5),(i); P.L. 119-21 (OBBBA) |
| `REVPROC_2009_20` | Rev. Proc. 2009-20 — Ponzi-type theft loss safe harbor | Rev. Proc. 2009-20 (95%/75% safe-harbor factors) |

---

## The form face (verbatim line map)

**SECTION A — Personal-Use Property (L1–18).** Header (verbatim): *"For tax years beginning after 2017, if you
are an individual, casualty or theft losses of personal-use property are deductible only if the loss is attributable
to a federally declared disaster."* FEMA DR-/EM- declaration-number field. L1–12 **per event** (separate 4684 each);
L13–18 aggregate on ONE 4684.
- L2 cost/other basis · L3 insurance or reimbursement (whether or not claimed) · **L4 gain** if L3 > L2 (skip L5–9)
- L5 FMV before · L6 FMV after · **L7 = L5 − L6** (FMV decline) · **L8 = smaller of L2 or L7** · **L9 = L8 − L3**, floored 0
- L10 = Σ L9 (cols A–D) · **L11 = $100 ($500 if qualified-disaster rules apply)** · **L12 = L10 − L11**, floored 0
- L13 = Σ all L4 gains · L14 = Σ all L12 losses · **L15** compares 13 vs 14 (net gain → **Schedule D**; qualified-
  disaster $500 losses → **Sch A line 16**, add standard deduction if not itemizing) · L16 = (L13 + L15) subtracted from L14
- **L17 = 10% of AGI** · **L18 = L16 − L17**, floored 0 → **Schedule A line 15**

**SECTION B — Business & Income-Producing Property.**
*Part I (L19–28), per event:* L20 cost/adj basis · L21 insurance · **L22 gain** if L21 > L20 (skip 23–27) · L23 FMV
before · L24 FMV after · **L25 = L23 − L24** · **L26 = smaller of L20 or L25** *(NOTE: total destruction / theft →
enter full L20 basis, ignore FMV)* · **L27 = L26 − L21**, floored 0 · L28 = Σ L27 → line 29 or 34.
*Part II (L29–39), holding-period split → §1231/ordinary:*
- **Held ≤1 yr:** L29 entries · L30 totals · **L31 = combine L30 (b)(i)+(c) → Form 4797 line 14** (ordinary) · L32 =
  L30 (b)(ii) income-producing → **Sch A line 16**
- **Held >1 yr:** L33 gains from 4797 L32 · L34 entries · L35 total losses · L36 total gains (L33+L34(c)) · L37 = Σ
  L35 · **L38a** if losses > gains → 4797 line 14 (ordinary) · L38b = L35(b)(ii) → Sch A line 16 · **L39** if gains ≥
  losses → **4797 line 3** (§1231 capital gain). Partnerships → 1065 Sch K L11; S-corps → 1120-S Sch K L10.

**SECTION C — Ponzi-type theft (L40–51).** Rev. Proc. 2009-20: L40 initial + L41 subsequent investment + L42 prior-
year income − L44 withdrawals = **L45 total qualified investment** · **L46 = 0.95 (no third-party recovery) or 0.75
(potential recovery)** · L47 = L46 × L45 · L48 actual + L49 potential recovery = L50 · **L51 = L47 − L50 = deductible
theft loss → Section B Part I line 28** (skip 19–27).

**SECTION D — §165(i) election to deduct a federally declared disaster loss in the PRECEDING year (L52–57).** Election
statement (disaster, dates, address) + revocation (Oct 13 2016 rules). Filing-mechanics election, not a compute.

---

## Verified 2025 constants (year-keyed — re-verify each season)

| item | 2025 value | note |
|---|---|---|
| Personal per-event floor | **$100** | L11 |
| Personal aggregate AGI floor | **10% of AGI** | L17 |
| Qualified-disaster floor | **$500** (replaces $100) | L11; no 10%-AGI; add to standard deduction |
| **Qualified-disaster declaration window** | **declared 1/1/2020 – 9/2/2025**; incident began on/before **7/4/2025**, ended by **8/3/2025** | ▲ OBBBA (P.L. 119-21) extended it. **The load-bearing year-keyed item** — churns every season. COVID-only declarations excluded. |
| Ponzi safe-harbor factor | **95%** (no potential recovery) / **75%** (potential recovery) | L46, Rev. Proc. 2009-20 |

---

## The §165(h)(5) limitation + OBBBA (the load-bearing law question)

- **Personal casualty/theft loss (Section A) is deductible ONLY if attributable to a federally declared disaster** —
  in effect for TY2025 (form header, "tax years beginning after 2017", no stated sunset). **Personal casualty GAINS
  are the exception** — they can be offset by otherwise-nondeductible personal losses.
- **OBBBA (P.L. 119-21) EXTENDED the qualified-disaster special rules** ($500 floor / no-10%-AGI / standard-deduction
  add-back) to declarations through **9/2/2025** (i4684 "What's New" verbatim). It did NOT repeal the base FDD
  limitation and did NOT add state-declared disasters.
- **NEW — financial-scam theft losses (OBBBA, i4684 "What's New"):** a victim of a financial scam entered into for
  profit may claim a **theft loss** if (1) the loss is criminal theft under applicable state law, (2) no reasonable
  prospect of recovery, (3) the transaction was entered into **for profit**. Reported in **Section B** (income-
  producing) — NOT Section A — so it is **not** subject to the FDD limitation.
- **§165(i) preceding-year election** = unchanged (Section D). **Filing Relief for Natural Disasters Act** expanded
  mandatory deadline postponement for disasters declared after 7/24/2025 (deadline relief, not a compute change).

---

## Compute mechanics (for rules/diagnostics)

- **Per-property loss** = min(adjusted basis, FMV decline = FMV before − FMV after) − insurance/reimbursement, floored
  at 0. Section A: L8/L9. Section B: L26/L27. **Total destruction / theft of business property → use FULL basis** (L26 = L20).
- **Gain** when reimbursement > basis (L4 / L22). Personal net gain → Schedule D; business gains → 4797 §1231 netting.
- **Insurance counts whether or not a claim was filed;** a *reasonable prospect of recovery* defers the loss until
  ascertainable (loss not "sustained"); failure to file a timely claim bars the covered portion.
- **Section B §1231 routing:** ≤1 yr → ordinary (4797 L14); >1 yr losses>gains → ordinary (4797 L14); >1 yr gains≥
  losses → §1231 capital (4797 L3). Theft of business property netted the same way.

---

## Proposed scope for the Gate-1 walk (compute vs defer)

1. **Section A personal** — compute the full flow (per-property loss, $100 floor, FDD-limitation gate, 10%-AGI floor)
   AND the qualified-disaster $500/no-AGI/standard-deduction special path with the year-keyed declaration window.
2. **Section B business** — compute Part I per-property loss/gain + Part II holding-period §1231/ordinary netting and
   the routing to Form 4797 (L3/L14) / Schedule A; direct-entry the 4797 linkage (flow assertions).
3. **Sections C & D** — Section C Ponzi = compute the Rev. Proc. 2009-20 safe harbor (95%/75%); Section D §165(i)
   election = structure + diagnostic (filing-mechanics, not a compute).
4. **Entity types + the new financial-scam theft loss** — one `4684` form serving personal (Section A, 1040) +
   business casualty (Section B, all entities); model the OBBBA financial-scam theft loss as a Section B diagnostic
   with the 3 conditions.
