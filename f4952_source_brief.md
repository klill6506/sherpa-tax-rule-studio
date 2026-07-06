# Source Brief — Form 4952, Investment Interest Expense Deduction (TY2025)

**WO-17 · SPINE S-16 (4th item after 8990 + Schedule H + 4684) · greenfield RS-first**
Research pass 2026-07-06, verbatim vs FINAL 2025 Form 4952. Nothing carried [UNVERIFIED].

---

## Sources

| source_code | title | citation |
|---|---|---|
| `IRS_2025_F4952` | 2025 Form 4952 — Investment Interest Expense Deduction (instructions on pp. 3-4) | Form 4952 (2025), Cat. No. 13177Y, **Created 5/28/25**, Attach. Seq. No. 51. **No separate i4952 — instructions are pp. 3-4 of the form PDF.** |
| `IRC_163D` | IRC §163(d) — limitation on investment interest | 26 U.S.C. §163(d)(1)-(5) |

---

## The form face (verbatim line map)

**Part I — Total Investment Interest Expense**
- **L1** investment interest expense paid/accrued in 2025 · **L2** disallowed investment interest carryforward from 2024
  Form 4952 line 7 · **L3 = L1 + L2** total investment interest expense

**Part II — Net Investment Income**
- **L4a** gross income from property held for investment (EXCLUDING net gain from disposition) · **L4b** qualified
  dividends included on 4a · **L4c = L4a − L4b**
- **L4d** net gain from disposition of investment property · **L4e** smaller of 4d or net capital gain from that
  disposition · **L4f = L4d − L4e**
- **L4g** amount from 4b and 4e ELECTED to include in investment income (≤ 4b + 4e) · **L4h = L4c + L4f + L4g** investment income
- **L5** investment expenses · **L6 = max(0, L4h − L5)** net investment income

**Part III — Investment Interest Expense Deduction**
- **L7 = max(0, L3 − L6)** disallowed carryforward to 2026 (INDEFINITE — feeds next year's L2) · **L8 = min(L3, L6)**
  investment interest expense deduction → **Schedule A line 9** (1040) / **Form 1041 line 10** (estate/trust)

**Invariants (diagnostic-ready):** L3=1+2 · L4c=4a−4b · L4f=4d−4e · L4h=4c+4f+4g · L6=max(0,4h−5) · L7=max(0,3−6) ·
L8=min(3,6). Bounds: 4e ≤ 4d · 4g ≤ (4b + 4e).

---

## The core: §163(d) limitation (the heart)

- Investment interest is deductible **only up to net investment income** (§163(d)(1)). **L8 = smaller of L3 or L6.**
- The excess (**L7 = L3 − L6**) is disallowed and **carries forward INDEFINITELY** (§163(d)(2)) — mechanically proven
  by L2 pulling "Disallowed investment interest expense from 2024 Form 4952, line 7" with no year cap.

## The 4g net-capital-gain / qualified-dividends election

- **Default:** qualified dividends (4b) and net capital gain (4e) are EXCLUDED from investment income (only 4c ordinary
  income + 4f short-term/ordinary gain count via 4h).
- **Election (L4g):** elect to include part/all of 4b + 4e in investment income → raises the L6 ceiling → more
  investment interest deductible NOW. **Cost (verbatim CAUTION):** the elected amount is NOT eligible for the
  qualified-dividends / capital-gains preferential rate (taxed at ordinary rates). Coordinated with the Schedule D
  Tax Worksheet line 3 (1040) / Sch D (1041) line 25 / QD Tax Worksheet line 3 (1041). Ordering default: attributable
  first to net capital gain (4e), then qualified dividends (4b). Revocable only with IRS consent.

---

## Definitions / mechanics (for diagnostics)

- **Investment interest (L1):** interest on debt to buy/carry property held for investment (incl. K-1 investment
  interest). **EXCLUDES:** personal/qualified-residence interest (§163(h)); passive-activity interest (Form 8582);
  capitalized interest (§263A); interest allocable to tax-exempt income (§265); §264 (post-6/8/1997 insurance/annuity).
- **Property held for investment:** produces interest/dividends/annuities/royalties not in the ordinary course of a
  trade/business; EXCLUDES an interest in a passive activity (working-interest oil/gas exception).
- **Gross investment income (L4a):** interest + ordinary dividends (except Alaska Permanent Fund) + annuities +
  royalties, not in ordinary course; incl. K-1 + estate/trust net investment income. Net disposition gain goes to 4d.
- **Line 5 investment expenses (post-TCJA — key diagnostic):** allowed non-interest deductions directly connected to
  producing investment income (e.g., depreciation/depletion). Verbatim CAUTION: **do NOT include 2%-floor
  miscellaneous itemized deductions — suspended for tax years after 12/31/2017 and before 1/1/2026.** For TY2025 they
  remain excluded; OBBBA §67(g) made the suspension PERMANENT (the 2025 form still prints the old TCJA sunset wording —
  no compute change, watch the 2026 wording).
- **Who must file / exception:** an individual/estate/trust with investment interest files 4952. **No 4952 required if
  ALL:** (1) investment income (interest + ordinary dividends − qualified dividends) > investment interest expense;
  (2) no other deductible investment expenses; (3) no disallowed-interest carryover from 2024.

## OBBBA / 2025 law changes

**§163(d) itself: NO CHANGE for TY2025** (no "What's New" on the form). OBBBA's interest changes are §163(j) **business**
interest (Form 8990) — a different provision, do not conflate. The only adjacent OBBBA item is §67(g) misc-itemized
permanence (affects the L5 exclusion, already the case for 2025).

---

## Proposed scope for the Gate-1 walk (compute vs defer)

1. **Core compute (baseline)** — Part I/II/III full compute: L3, L4c/L4f/L4h, L6, and the §163(d) limitation (L8 =
   min(L3, L6)) + the indefinite carryforward (L7 = max(0, L3 − L6)).
2. **4g election** — compute the election mechanic (4h includes the direct-entered elected amount, capped at 4b + 4e,
   ordering 4e-then-4b) + a diagnostic on the rate trade-off (elected amounts lose the preferential rate) and the
   Schedule D Tax Worksheet coordination.
3. **Entity types + routing** — one `4952` form, entity_types [1040, 1041]; L8 → Schedule A line 9 (1040) / Form 1041
   line 10 (trust/estate); the "not required to file" 3-condition exception as a diagnostic.
4. **Line 5 + exclusions** — model L5 with the misc-itemized-suspension diagnostic (through 2025, OBBBA-permanent) +
   an investment-interest exclusion diagnostic (qualified-residence / passive / tax-exempt / §264 / §265).
