# Source Brief — Form 8379, Injured Spouse Allocation

**WO-18 · SPINE S-16 (5th item after 8990 + Sch H + 4684 + 4952) · greenfield RS-first**
Research pass 2026-07-06, verbatim vs FINAL IRS sources. **Ken's "8679" = a typo; the form is 8379** (both 404 in prod).

---

## Sources

| source_code | title | citation |
|---|---|---|
| `IRS_F8379` | Form 8379 — Injured Spouse Allocation | Form 8379 (**Rev. 11-2023**), Cat. No. 62474Q, Attach. Seq. No. 104 (current — no annual reissue) |
| `IRS_I8379` | Instructions for Form 8379 | Instructions for Form 8379 (**Rev. 11-2024**) |
| `IRC_6402` | IRC §6402(c)-(e) — Treasury offset / overpayment application | 26 U.S.C. §6402(c),(d),(e) |

---

## What this is (concept)

An **injured spouse** is a spouse on a joint return whose share of the joint overpayment (refund) was/will be applied
(offset, §6402) against the **OTHER** spouse's separate, legally enforceable past-due debt. Form 8379 recovers the
injured spouse's share. **NOT Form 8857 (innocent spouse — relief from joint LIABILITY for the other spouse's
erroneous items).** Different form, different remedy — the boundary is flagged on the form (Part I line 3/4 Notes).

The six offsettable debts (Part I line 3, verbatim): **federal tax · state income tax · state unemployment
compensation · child support · spousal support · federal nontax debt (e.g., student loan).**

---

## The form face (verbatim line map, Rev. 11-2023)

**Part I — Should You File This Form? (eligibility decision tree)**
- **L1** tax year · **L2** file a joint return? (No → STOP, not injured) · **L3** did/will the IRS use the joint
  overpayment for a past-due debt owed ONLY by your spouse? (No → STOP) · **L4** are YOU legally obligated to pay it?
  (**Yes → STOP, not injured**; consider innocent spouse) · **L5** resident of a community-property state at any time?
  (**Yes → name the state(s), SKIP L6-9, go to Part II**) · **L6** made & reported payments (withholding/estimated)?
  (Yes → Part II) · **L7** earned income (wages/SE)? (No → L9) · **L8** claim EIC or additional child tax credit?
  (Yes → Part II) · **L9** claim a refundable credit? (Yes → Part II; **No → STOP, not injured**).
  **Injured-spouse qualification = reach Part II via L5 (community property) OR L6 (payments) OR L8 (EIC/ACTC) OR L9
  (other refundable credit).**

**Part II — Information About the Joint Return**
- **L10** names/SSNs in joint-return order + "if injured spouse, check here" (each spouse) · **L11** issue refund in
  both names? (else separate refunds) · **L12** mail injured-spouse refund to a different address?

**Part III — Allocation Between Spouses (the constraint heart).** Three columns per line: **(a) amount on joint
return · (b) allocated to injured spouse · (c) allocated to other spouse**, with **col (a) = (b) + (c)** on every line.
- **L13a** income on Form(s) W-2 · **L13b** all other income · **L14** adjustments to income · **L15** standard OR
  itemized deductions · **L16** nonrefundable credits · **L17** refundable credits (**EXCLUDE any EIC**) · **L18**
  other taxes · **L19** federal income tax withheld · **L20** payments.

**Part IV — Signature** (only if filed BY ITSELF, not with the return).

---

## Allocation rules (for diagnostics — i8379 Rev. 11-2024)

- **L13a W-2 income:** to the spouse who earned it. **L13b other income:** joint income (e.g., joint-account
  interest) allocated as the taxpayers determine.
- **L14 adjustments:** to the spouse who would have claimed it on a separate return.
- **L15 standard deduction:** **one-half of the BASIC standard deduction to each** (50/50); the additional standard
  deduction (age/blindness) to the individual spouse who qualifies.
- **L16/L17 dependent-driven credits:** CTC / ODC / child-&-dependent-care / education credits to the spouse who
  would have claimed the qualifying child/relative on a separate return.
- **L18 other taxes:** SE tax to the spouse who earned the SE income.
- **L19 federal income tax withheld:** to each spouse per their own Forms W-2/W-2G/1099 (**withholding follows the
  income**).
- **L20 estimated payments:** any split both spouses agree to.
- **EIC:** NOT on Part III — the **IRS allocates the EIC itself**. And the **IRS computes the final refund share** from
  the Part III allocation (the form allocates items; it does not compute the refund).

## Community-property-state override (critical diagnostic)

- The **nine** community-property states (i8379): **Arizona, California, Idaho, Louisiana, Nevada, New Mexico, Texas,
  Washington, Wisconsin.**
- **Override:** the IRS does NOT necessarily follow the Part III entries — "we divide the refund based on state
  community property law" (irs.gov). Generally 50% of a joint overpayment (except EIC) goes to non-federal-tax debts;
  state law varies for federal-tax-debt offsets. This is why **L5 routes community-property filers straight to Part II**
  (skipping the L6-L9 income tests).

## Filing mechanics (for diagnostics)

- **When/how:** with the joint return (paper or e-file), with a 1040-X, or by itself after learning of the offset.
- **Time limit:** **within 3 years from the return filing (incl. extensions) OR 2 years from the date the tax was
  paid, whichever is later.**
- **Processing:** ~14 weeks (paper with return) · ~11 weeks (e-filed with return) · ~8 weeks (by itself).

## Law changes

**None affecting Form 8379** — purely procedural (allocation of already-computed items), untouched by OBBBA. Authority
is §6402(c)-(e) (Treasury offset), NOT §1.6015 (that governs innocent spouse / Form 8857).

---

## Proposed scope for the Gate-1 walk (compute vs defer)

1. **Part I eligibility** — compute the L2→L9 decision tree → an `is_injured_spouse` determination + a stop-reason
   diagnostic for each fail (not a joint return / debt not spouse-only / you're legally obligated / no qualifying path).
2. **Part III allocation** — validate the **col (a) = (b) + (c)** constraint on every line (reconciliation rules) +
   encode the allocation rules as diagnostics (W-2 to earner, withholding follows income, standard deduction 50/50,
   dependent credits to the claiming spouse, EIC excluded); **do NOT estimate the injured spouse's refund share** (the
   IRS computes it — a spec estimate would be a guess).
3. **Community-property override** — encode the 9 states + the override gate (Part III may not control; L5 skips L6-9).
4. **Boundaries + mechanics** — the 8379-vs-8857 boundary, the 3yr/2yr time limit, the standalone Part IV path, and
   processing times as diagnostics; one `8379` form, entity_types [1040].
