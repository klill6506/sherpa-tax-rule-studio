# Form 8888 Source Brief — Allocation of Refund
*Research pass 2026-07-13 (tts s77 / payment-cluster draft-to-gate batch order 2). Gap re-confirmed
2026-07-13: `lookup/8888/export/` = 404.*

## Authoritative sources (fetched/verified 2026-07-13)

| Source | Revision | Verified how |
|---|---|---|
| Form 8888 (instructions INCLUDED — 3-page PDF) | **Rev. December 2025** ("Created 11/20/25"), **continuous-use** ("converted from annual revision to continuous use") | f8888.pdf downloaded from irs.gov/pub/irs-pdf 2026-07-13, pymupdf extraction |
| About page | Recent Developments: **"None at this time"** (reviewed 23-Apr-2026) | fetched 2026-07-13 |
| MeF business rules | 1040_Business_Rules_2025v5.3.csv — F8888-* family | grepped 2026-07-13 |
| MeF schema | IRS8888.xsd 2025v5.3 IndividualIncomeTax/Common — ReturnData1040 slot ~1958 | parsed 2026-07-13 |

## The two structural catches (title changed meaning)

1. **The savings-bond program is DISCONTINUED** (form Reminders, Rev. 12-2025 verbatim): "The
   program allowing for your refund to be deposited into your TreasuryDirect® account to buy
   savings bonds, as well as the ability to buy paper bonds with your refund, has been
   discontinued. **Form 8888 is now only used to split your direct deposit refund between two or
   more accounts.**" The face's Part-II-era line 4 prints **"Reserved for future use"**; the old
   check line is gone. The 2025v5.3 XSD **dropped the SavingsBondPurchaseInfoGrp entirely** and
   every bond business rule (F8888-005/-009 through -014, -017/-018) is **Disabled**;
   `RefundByCheckAmt` survives as a schema element but **F8888-023 (Active) forbids any value**.
2. **EO 14247** (What's New): starting **October 2025** the IRS generally stops issuing paper
   checks for federal disbursements including refunds, unless an exception applies
   (irs.gov/ModernPayments).

## Face (Rev. 12-2025) — three deposit groups + the total

- **1a/2a/3a** amount to each account (each deposit **at least $1**; may allocate the entire
  refund to one... no — "your entire deposit may be deposited in one account" refers to the
  fallback; a SINGLE-account request shouldn't file 8888 at all: "If you want your refund
  deposited to only one account, don't complete this form. Instead, request direct deposit on
  your tax return.")
- **1b/2b/3b** routing number — 9 digits, first two **01-12 or 21-32**.
- **1c/2c/3c** account type — exactly ONE of Checking/Savings ("Don't check more than one box";
  IRA/HSA/brokerage → ask the institution which box).
- **1d/2d/3d** account number — ≤17 chars, hyphens included, no spaces/symbols.
- **4** Reserved for future use.
- **5** = 1a+2a+3a, "must equal the refund amount shown on your tax return" (also the F8888-001-04
  /-002-03 rejects; a different total "may delay your refund").

## Eligibility / account rules (form text verbatim substance)

- Accounts: checking/savings/other at a U.S. bank, mutual fund, brokerage, credit union —
  including **traditional/Roth/SEP IRA (NOT SIMPLE), HSA, Archer MSA, Coverdell ESA**.
- **Form 8379 (injured spouse) bars the split** ("You can't have your refund deposited into more
  than one account if you file Form 8379").
- **Account must be in your name** — never the preparer's account ("don't have any part of your
  refund deposited into the preparer's account to pay the fee").
- **Three direct deposits per account/prepaid card per year** (irs.gov Direct-Deposit-Limits).
- Joint-return caution: the spouse may get at least part of the refund.
- **IRA deposits**: establish the IRA first; notify the trustee of the target year; a prior-year
  designation must actually post by the un-extended due date or the contribution fails → amend
  (the printed 2023/2024 example).

## Fallback / adjustment ordering (printed rules — pinned as scenarios)

- **Rejected or delayed**: everything lands in the **last valid account listed** ("make sure the
  last account you list... is an account you would want the entire refund deposited in").
- **Math-error INCREASE** → added to the **last** listed account (printed example: $300 split
  100/100/100, refund becomes $350 → line 3 gets $150 total).
- **Math-error DECREASE** → stripped **from line 3, then line 2, then line 1** (printed example:
  $300 split 100/100/100, decrease $150 → line 3 loses its $100, line 2 drops to $50).
- **Past-due FEDERAL tax offset** → same 3→2→1 ordering.
- **OTHER offsets (BFS: state tax, child/spousal support, student loans)** → deducted from the
  account with the **LOWEST routing number first**, then next-lowest, then highest.
- Appeal-upheld math-error refund → deposited to the **line 1** account.
- Caution: an adjusted deposit to a contribution-limited account (IRA/HSA/MSA/ESA) or a deposit
  claimed as a deduction that never posts → corrective contribution or amended return.

## MeF (IRS8888 — ReturnData1040 document, slot ~1958)

Schema: `DirectDepositInfoGroup` **minOccurs=0 maxOccurs=3** {DirectDepositRefundAmt,
RoutingTransitNum, BankAccountTypeCd (Checking/Savings), DepositorAccountNum};
RefundByCheckAmt (forbidden by rule); TotalAllocationOfRefundAmt. Active rules:
- **F8888-001-04**: Σ DirectDepositRefundAmt == TotalAllocationOfRefundAmt.
- **F8888-002-03**: TotalAllocationOfRefundAmt == the return's RefundAmt.
- **F8888-015**: DepositorAccountNum unique across groups.
- **F8888-016**: DepositorAccountNum not all zeros.
- **F8888-020**: amended/superseded returns cap the total at 999,999,999.
- **F8888-023**: RefundByCheckAmt must NOT have a value.
Bond rules all Disabled; the bond group no longer exists in the XSD.

tts note: the 1040 line-35a face carries the "Check here if Form 8888 is attached" checkbox —
the tts leg wires it with the document (print + XML both).

## Boundaries (stated, not built)

- TreasuryDirect / paper-bond history — retired program, spec records the discontinuation only.
- Form 8379 interplay — the bar is a diagnostic; 8379 itself is a separate (unbuilt) form.
- Prepaid cards / mobile apps as deposit targets (form allows if RTN/acct provided) — no special
  handling; the preparer supplies numbers.
