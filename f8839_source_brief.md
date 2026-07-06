# Source Brief — Form 8839, Qualified Adoption Expenses (TY2025)

**WO-20 · SPINE S-16 (7th item after 8990 + Sch H + 4684 + 4952 + 8379 + 8814) · greenfield RS-first**
Research pass 2026-07-06, verbatim vs FINAL 2025 Form 8839. **★ Headline 2025 change: the credit is now partly REFUNDABLE (OBBBA).**

---

## Sources

| source_code | title | citation |
|---|---|---|
| `IRS_2025_F8839` | 2025 Form 8839 — Qualified Adoption Expenses | Form 8839 (2025), Cat. No. 22843L, **Created 9/2/25**, Attach. Seq. No. 38 |
| `IRS_2025_I8839` | 2025 Instructions for Form 8839 | Instructions for Form 8839 (2025), reviewed 30-Apr-2026 |
| `IRC_23_137` | IRC §23 / §36C (adoption credit + refundable) + §137 (employer exclusion); OBBBA §70402/§70403 | 26 U.S.C. §23, §36C, §137; P.L. 119-21 §70402, §70403 |

---

## What this is

Two independent computations (Purpose of Form, verbatim: *"figure your adoption credit and any employer-provided
adoption benefits you can exclude... you can't claim both a credit and exclusion for the same expenses"*):
- **Part II — Adoption CREDIT (§23/§36C)** for qualified adoption expenses, capped $17,280/child, MAGI-phased, split
  2025 into a **refundable** portion (up to $5,000/child) + a **nonrefundable** portion (tax-limited, 5-yr carryforward).
- **Part III — EXCLUSION (§137)** for employer-provided adoption benefits (W-2 box 12 code T), same cap + phaseout.

## ★ THE 2025 OBBBA CHANGE — REFUNDABILITY (verified)

**i8839 "What's New" (verbatim):** *"Up to $5,000 of adoption credit is refundable... determined separately for each
eligible child."* + **tribal parity** (§70403: state AND Indian tribal government special-needs determinations both
recognized). **Effective 2025** (OBBBA §70402, tax years beginning after 12/31/2024). New **lines 11a/11b/11c → line
13** ("Refundable adoption credit" → **Form 1040 line 30**). The **nonrefundable remainder retains the 5-year
carryforward** (line 18 → Schedule 3 line 6c). The **refundable portion is NOT carried forward**, and a **2024
carryforward remains nonrefundable** (Purpose-of-Form item 4).

**⚠ Provenance flag:** the $5,000 refundable cap being INDEXED is statutory (§36C / OBBBA §70402; the 2026 COLA figure
is $5,120) but is **NOT stated in the 2025 i8839** — cite the statute for the indexing claim, the form for the flat 2025 $5,000.

---

## Verified 2025 constants (INDEXED — re-verify each season)

| item | 2025 | line |
|---|---|---|
| Maximum credit per child | **$17,280** | L2 |
| Maximum exclusion per child | **$17,280** | L19 |
| MAGI phaseout BEGIN | **$259,190** | L8 / L26 |
| MAGI fully phased out at | **$299,190** ($259,190 + $40,000) | What's New |
| Phaseout divisor | **$40,000** | L9 / L27 |
| Refundable-portion cap per child | **$5,000** (2025; §36C-indexed, $5,120 for 2026 — NOT in i8839) | L11b |

---

## The form face (verbatim line map)

**Part I — child info (L1 cols a–g):** (c) born before 2008 & disabled · (d) special-needs child · (e) foreign child
· (f) identifying number · (g) adoption final in 2025 or earlier.

**Part II — Adoption Credit (per child, then totaled):**
- **L2 = $17,280** max · L3 prior-year expenses same child · **L4 = L2 − L3** · L5 qualified adoption expenses ·
  **L6 = min(L4, L5)** · L7 MAGI · **L8 = L7 − $259,190** (if > threshold; else L10 = 0) · **L9 = L8 ÷ $40,000**
  (decimal ≤ 1.000) · **L10 = L6 × L9** (reduction) · **L11a = L6 − L10** (credit after phaseout)
- **L11b = min(L11a, $5,000)** (refundable cap/child) · **L11c = Σ L11b** · **L12 = Σ L11a**
- **L13 = refundable = L11c → Form 1040 line 30** · **L14 = L12 − L13** · L15 prior-year carryforward · **L16 = L14 +
  L15** · L17 tax-liability limit (Credit Limit Worksheet) · **L18 = nonrefundable = min(L16, L17) → Schedule 3 line
  6c**; excess carries forward **5 years**.

**Part III — Employer-Provided Adoption Benefits (§137):**
- **L19 = $17,280** max exclusion · L20 prior-year benefits · **L21 = L19 − L20** · L22 employer benefits (W-2 box 12
  code T) · L23 = Σ L22 · **L24 = min(L21, L22)** *(special-needs child final 2025 → L21 full)* · L25 MAGI · L26 = L25
  − $259,190 · L27 = L26 ÷ $40,000 · L28 = L24 × L27 · **L29 = excluded = L24 − L28** · L30 = Σ L29 · **L31 = taxable =
  L23 − L30 → Form 1040 line 1f** (negative if L30 > L23).

---

## Compute mechanics (for rules/diagnostics)

- **Phaseout (per child):** fraction = min(1.000, max(0, (MAGI − $259,190) / $40,000)); credit after = L6 × (1 −
  fraction). MAGI ≤ $259,190 → 0; ≥ $299,190 → fully phased out. Same in Part III (L25-29).
- **Refundable/nonrefundable split (NEW):** refundable = min(L11a, $5,000)/child → L13 → 1040 L30; nonrefundable =
  (Σ L11a − L13 + prior carryforward), capped by the Credit Limit Worksheet → L18 → Sch 3 6c; excess carries fwd 5 yrs.
- **Special-needs:** full **$17,280** for a U.S. special-needs child finalized in 2025 even if expenses were less.
  OBBBA §70403 added tribal-government parity to *who determines* special needs — no change to the full-credit rule.
- **§137 ↔ §23:** both allowed, but NOT for the same expenses (employer-reimbursed amounts reduce L5 qualified expenses).
- **MFS:** married generally must file jointly (exception: legally separated / living apart). A separate filer may still claim a prior-year carryforward.

---

## Proposed scope for the Gate-1 walk (compute vs defer)

1. **Part II credit + the NEW refundable split** — compute L4-L18: max/expenses, MAGI phaseout, the refundable
   portion (min $5,000/child → L13 → 1040 L30), and the nonrefundable portion (+carryforward, capped by the tax-
   liability limit L17 → Sch 3 6c, 5-yr carryforward). Direct-entry the Credit Limit Worksheet figure (L17).
2. **Part III exclusion (§137)** — compute the employer-benefit exclusion + its own phaseout → excluded (L29) +
   taxable (L31 → 1040 line 1f).
3. **Special-needs + coordination diagnostics** — compute the special-needs full-credit override; diagnostics for the
   §137/§23 same-expense rule, the MFS restriction, and OBBBA tribal parity.
4. **Refundable-cap $5,000 (year-keyed + provenance) + carryforward baseline** — year-key the $5,000 (cite statute for
   indexing, form for the flat 2025 figure); one `8839` form [1040]; diagnostics for refundable-not-carried-forward +
   2024-carryforward-stays-nonrefundable + the 5-year carryforward.
