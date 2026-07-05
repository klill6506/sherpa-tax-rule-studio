# Boundary Diagnostics — Source Brief (S-5 / WO-04)

*Opened 2026-07-05 through the WORK_ORDERS front door. Module = the Core boundary diagnostics
(PRODUCT_MAP): Core never goes silent when a return crosses into module territory — it must
DETECT the boundary and throw a loud diagnostic naming what the return needs. Authorities
verified verbatim (research pass 2026-07-05); NOT from memory. OBBBA changed NONE of these
mechanics (it touched depreciation/§179/QBI, not M-3 / K-2-K-3 / Subchapter K basis).*

## Gap-check (front-door step 1)
Four of five boundaries already exist as RED-defers on the 1065 forms; two are genuine gaps.
- **M-3 threshold** — EXISTS: `D_L_M3` / `R-L-M3` on 1065_L (sourced). Verify 1120-S ($10M) equivalent.
- **§754 / §743(b) / §734(b)** — EXISTS: 1065_B Q10 + `IRC_754` (basis-adjust math RED-deferred).
- **§704(c)** — EXISTS: `D_SCHK_704C` structure-only (item M/N).
- **K-2/K-3** — PARTIAL: `D_SCHK_K3` is a **blanket "out of scope" flag**. **GAP: the DFE-fail determination**
  (PRODUCT_MAP makes "record WHY K-2/K-3 aren't required" CORE season one).
- **Multistate apportionment (beyond-licensed-state)** — **GAP: no indicator.**
- (§461(l) boundary = DONE via S-6 Form 461; 1041 Sch I AMT = defer to S-11 per D-2.)

---

## Verified trigger conditions

### B1 — Schedule M-3 threshold
- **Form 1065** — M-3 required if ANY: (1) Schedule L line 14 total assets **≥ $10M**; (2) **adjusted**
  total assets **≥ $10M**; (3) total receipts **≥ $35M**; (4) a **reportable entity partner** owns/deemed-owns
  **≥ 50%** of capital/profit/loss. REP = 50%+ owner that itself filed M-3 on its last return. Voluntary filing
  allowed. *Source: Instructions for Schedule M-3 (Form 1065), Rev. 11/2023 (NOT annually reissued — controlling
  for TY2025; re-confirm each season).*
- **Form 1120-S** — M-3 required if total assets **≥ $10M** (single test; no receipts/REP prong). At **≥ $50M**
  complete M-3 entirely; $10M–$50M may do Part I + M-1. *Source: Instructions for Schedule M-3 (Form 1120-S),
  Rev. 12/2019 (latest issued; controlling for TY2025 — do NOT cite the 1120 June-2025 revision for an S corp).*

### B2 — K-2/K-3 Domestic Filing Exception (Form 1065) — fires when the DFE FAILS
Partnership need NOT file K-2/K-3 only if ALL FOUR are met (2025 i1065 K-2/K-3 instructions):
1. **No/limited foreign activity** — no foreign activity, or only passive-category foreign income with **≤ $300**
   foreign tax credit and shown on a payee statement.
2. **Only listed U.S.-person direct partners** — individuals (citizens / resident aliens), certain domestic
   estates/trusts, S corps (sole shareholder), SMLLCs, domestic partnerships of such partners. (2025 broadened this list.)
3. **Partner notification** — by the K-1 furnish date, stating no K-3 will be provided unless requested.
4. **No K-3 request by the "1-month date"** — 1 month before the 1065 is filed (calendar-year on extension ≈ Aug 17, 2026).
   (2025: a late request no longer carries forward to subsequent years.)
**Diagnostic fires RED when any criterion is NOT met** → international reporting required, not supported season one.
*Source: 2025 Partnership Instructions for Schedules K-2 and K-3 (Form 1065).*

### B3 — §704(c) built-in gain/loss (indicator, not a numeric threshold)
Fire when: (a) **forward §704(c)** — non-cash property contributed with **FMV ≠ adjusted tax basis** (a reasonable
method is MANDATORY, Reg §1.704-3(a)(1)); or (b) **reverse §704(c)** — a capital-account **book-up/book-down**
(revaluation) creating a book-tax disparity (Reg §1.704-3(a)(6)). Three methods: traditional / traditional-with-
curative / remedial (§1.704-3(b),(c),(d)). *Source: IRC §704(c); Treas. Reg. §1.704-3.*

### B4 — §754 / §743(b) / §734(b) (indicator + $250k mandatory triggers)
Fire when: (a) a **§754 election is on file** (every later interest transfer → §743(b), and property distribution
→ §734(b), now generates trackable basis adjustments); OR **mandatory even without an election** — (b) a
**substantial built-in loss > $250,000** on an interest transfer (§743(d)); OR (c) a **substantial basis reduction
> $250,000** on a distribution (§734(d)). A §754 election, once made, applies to that year and ALL subsequent
years (revocable only with IRS consent). *Source: IRC §§754, 743(d), 734(d).*

### B5 — Multistate apportionment (state-specific indicator; the one soft boundary)
Fire when an entity has income-tax nexus / apportionable activity in a state **beyond the supported set (GA +
SC/AL/NC/FL/TN)**. Screen on property/payroll/sales in a non-supported state. Common (MTC-model) factor-presence
benchmarks: property **> $50k**, payroll **> $50k**, sales **> $500k**, or 25% of the total — **but thresholds
VARY BY STATE**. The one federal anchor is **P.L. 86-272** (15 U.S.C. §381): a state may not impose a **net income
tax** where the only in-state activity is **solicitation of orders for tangible personal property** filled from
out of state (does NOT cover services/digital, franchise/gross-receipts taxes; increasingly eroded for internet
activity). *Source: P.L. 86-272 / 15 U.S.C. §381; MTC factor-presence model (illustrative, state-specific).*
⚠ Indicator-level only — exact per-state thresholds must be pulled per state and re-verified each season.

---

## Pending Gate-1 scope decisions
1. **Shape** — a new consolidated boundary-diagnostics form (single season-one "completeness critic") vs. amend
   each existing Core form in place vs. hybrid.
2. **K-2/K-3 DFE** — COMPUTE the 4-criteria DFE determination (fire RED on fail) vs. keep the blanket defer +
   document the criteria.
3. **Multistate apportionment** — indicator diagnostic (flag out-of-supported-state nexus + P.L. 86-272 note) vs. stub.
4. **Existing boundaries (M-3/§754/§704(c))** — re-encode with the verified/pinned thresholds in the chosen shape,
   or leave the existing form flags untouched and only build the two gaps.

*Status: GAP-CHECKED → DRAFTING (brief done) → AWAITING KEN (scope walk). Nothing seeds until Gate 1.*
