# Source Brief — Form 8814, Parents' Election To Report Child's Interest and Dividends (TY2025)

**WO-19 · SPINE S-16 (6th item after 8990 + Sch H + 4684 + 4952 + 8379) · greenfield RS-first**
Research pass 2026-07-06, verbatim vs FINAL 2025 Form 8814. Sibling of the EXISTING `8615` (child's kiddie-tax form).

---

## Sources

| source_code | title | citation |
|---|---|---|
| `IRS_2025_F8814` | 2025 Form 8814 — Parents' Election To Report Child's Interest and Dividends | Form 8814 (2025), Cat. No. 10750J, **Created 3/19/25**, Attach. Seq. No. 40 |
| `IRS_2025_I8814` | 2025 Instructions for Form 8814 | Instructions for Form 8814 (2025), reviewed 30-Apr-2026 |
| `IRC_1G` | IRC §1(g)(7) — parents' election / §1(g) kiddie tax + Pub 929 | 26 U.S.C. §1(g)(7); IRS Pub. 929 |

**⚠ Provenance caveat (from research):** the Form 8615 / §1(g) "alternative if no election" relationship is accurate
tax law but is **NOT stated in the 8814 form/instructions** — cite it to **§1(g) / Pub 929 / the existing 8615 spec**,
NOT to i8814.

---

## What this is

The parents' election (**§1(g)(7)**) to report a child's interest, dividends, and capital gain distributions on the
PARENTS' Form 1040 instead of the child filing. Purpose (verbatim): *"Use this form if you elect to report your
child's income on your return. If you do, your child will not have to file a return."* The alternative (no election)
is the child files **Form 8615** (already in RS prod — this closes the `D_8615_004` RED-defer loop). **Caution on the
form:** the tax *"may be less if you file a separate tax return for the child"* (the election forfeits the child's own
benefits — blind additional standard deduction, early-withdrawal penalty, the child's itemized deductions).

---

## Verified 2025 constants (INDEXED — re-verify every season)

| item | 2024 | **2025 (verified)** | line |
|---|---|---|---|
| Base amount / Part II heading threshold | $2,600 | **$2,700** | L5 / Part II heading |
| Amount not taxed (first tier) | $1,300 | **$1,350** | L13 |
| Flat tax on second tier (10% × $1,350) | $130 | **$135** | L15 "No" |
| Child gross-income upper limit (don't-file ceiling) | $13,000 | **$13,500** | L4 / eligibility |

---

## The form face (verbatim line map)

**Eligibility (all must hold, i8814):** child **under 19 (or under 24 if full-time student)** at end of 2025; child's
**only** income = interest + dividends (incl. capital gain distributions + Alaska Permanent Fund dividends); child's
**gross income < $13,500**; child **required to file**; child **does not file jointly**; **no estimated payments** for
the child (incl. prior-year overpayment applied); **no federal income tax withheld** (no backup withholding); you are
the **qualified parent** (MFJ / higher-income MFS / custodial). **A separate Form 8814 per child** (line C checked when >1).

**Part I — Child's Interest and Dividends To Report on Your Return**
- L1a taxable interest · L1b tax-exempt interest (not on 1a) · L2a ordinary dividends (incl. Alaska PFD) · L2b
  qualified dividends (incl. in 2a) · L3 capital gain distributions
- **L4 = L1a + L2a + L3.** *If ≤ $2,700 → skip L5-12, go to L13 (Part II only). If ≥ $13,500 → do NOT file (child
  files own return).*
- **L5 = $2,700** (base) · **L6 = L4 − L5** · **L7 = L2b ÷ L4** (decimal ≥3 places) · **L8 = L3 ÷ L4** (decimal) ·
  **L9 = L6 × L7** (qualified-dividend portion) · **L10 = L6 × L8** (cap-gain-distribution portion) · **L11 = L9 + L10**
  · **L12 = L6 − L11** (remaining ordinary) → **Schedule 1 line 8z, "Form 8814."**
- **Carries to the parent's return:** L9 → Form 1040 **lines 3a & 3b** (qualified/ordinary dividends); L10 → **Schedule D
  line 13** (or 1040 line 7 if Sch D not required); L12 → Schedule 1 line 8z.

**Part II — Tax on the First $2,700 of Child's Interest and Dividends**
- **L13 = $1,350** (not taxed) · **L14 = L4 − L13** (floored 0) · **L15 tax** = *if L14 ≥ $1,350 → $135; else L14 × 10%*
  → **Form 1040 line 16 (check box 1).** (If line C checked, combine per instructions.)

---

## Compute mechanics (for rules/diagnostics)

- **Three tiers:** first $1,350 not taxed; next $1,350 taxed at 10% (max **$135**); everything over **$2,700** carried
  to the parent's return (L6→L12).
- **Proportional split of the excess (L6):** the qualified-dividend fraction (L7 = L2b/L4) and cap-gain-distribution
  fraction (L8 = L3/L4) of the excess keep their character on the parent's return (L9 QD, L10 cap-gain dist); the
  remainder (L12) is ordinary → Schedule 1 line 8z.
- **Multiple children:** one 8814 each; line C aggregation.

## Law changes

**No substantive change for TY2025** — only routine inflation indexing of the four thresholds. No OBBBA mention.

---

## Proposed scope for the Gate-1 walk (compute vs defer)

1. **Part I allocation** — compute L4-L12 incl. the proportional QD (L9) / cap-gain-dist (L10) split and the
   parent-return carries (L9 → 1040 3a/3b, L10 → Sch D L13, L12 → Sch 1 L8z), year-keyed $2,700 base.
2. **Eligibility + threshold gates** — compute a `can_elect` determination from the 8 conditions + the two gates
   (L4 ≤ $2,700 → Part II only; L4 ≥ $13,500 → don't file) + the "may be cheaper to file separately" caution.
3. **8615 relationship + provenance** — a diagnostic cross-referencing Form 8615 (the child-files alternative),
   cited to **§1(g)/Pub 929** (NOT i8814, per the caveat); one `8814` form, entity_types [1040]; multiple-children.
4. **Part II tax (baseline)** — compute L13 $1,350 / L14 / L15 ($135 flat-or-10%) → Form 1040 line 16.
