# PAL / Basis Deepening — Source Brief (S-6 / WO-03)

*Opened 2026-07-05 through the WORK_ORDERS front door. Module = passive-activity-loss / at-risk /
excess-business-loss deepening. Mostly AMENDMENTS to existing specs (`FORM_8582`, `6198`) + one new
§461(l) diagnostic. Authorities verified verbatim against primary sources (research pass 2026-07-05);
NOT from memory. Per CLAUDE.md authoritative-source rule + tax-law-accuracy policy.*

## Gap-check (front-door step 1)
- **`FORM_8582`** exists — home `load_1040_schedule_e.py` (SCHEDULE_E + FORM_8582, "simplified v1
  bucket", 12 rules). R1/R2/R3 amend here.
- **`6198`** exists (integrated during the 4835 work). R4 references/amends.
- **§461(l)** — no `461` spec on disk → **R5 is the one genuinely new artifact** (new diagnostic/form).

---

## Verified authorities

### R1 — Self-rental recharacterization · **Treas. Reg. §1.469-2(f)(6)**
Net rental **income** (not loss) from an item of property rented to a trade/business activity in which
the taxpayer **materially participates** (§1.469-5T) is recharacterized **non-passive**. Key points:
**item-by-item** ("from an item of property"); **net income only** (a net loss stays passive — the
"heads-the-IRS-wins" asymmetry); gated on material participation in the **tenant** activity. Excludes
property already caught by (f)(5) (incidental-to-development, which uses *significant* participation).
Grouping under §1.469-4 can't convert self-rental net income back to passive. — *Source: 26 CFR
§1.469-2(f)(6).*

### R2 — PTP loss segregation · **IRC §469(k)**
§469 applied **separately to each publicly traded partnership** ((k)(1)). Consequence: a PTP net passive
loss offsets **only** net passive income **from that same PTP**; not other passive income, and non-PTP
passive income can't absorb PTP losses. Disallowed losses **suspend + carry forward** against that PTP's
future income; **freed only on full disposition** of the entire PTP interest (§469(g) coord. §469(k)(3);
partial disposition does not release). — *Source: 26 U.S.C. §469(k),(g).*

### R3 — Real Estate Professional · **IRC §469(c)(7) + Treas. Reg. §1.469-9**
Two tests, BOTH required: (i) **>½ of personal services** in trades/businesses are in real-property
trades/businesses in which the taxpayer materially participates; AND (ii) **>750 hours** in real-property
trades/businesses. **Spouse rule:** on a joint return either spouse must satisfy **both tests alone** —
spouses may **not** combine hours (contrast §469(h)(5), which counts a spouse's participation only for
the separate *material-participation* test). Qualifying removes the per-se-passive rule for rental real
estate, **but each rental interest is still tested for material participation** UNLESS the **§1.469-9(g)
election** to treat all rental real estate as a **single activity** is made. — *Source: 26 U.S.C.
§469(c)(7)(A)-(C); 26 CFR §1.469-9(e),(g).*

### R4 — At-risk limitation · **IRC §465 / Form 6198 (Rev. Nov 2025)**
**Ordering: §465 (at-risk) → §469 (passive) → §461(l) (EBL).** A §465-disallowed loss suspends and never
reaches the passive analysis that year. Amount at risk = cash + adjusted basis of contributed property +
borrowings for which **personally liable** (or non-activity property pledged, to net FMV) + **qualified
nonrecourse financing** for real property (§465(b)(6)). ⚠ **Caveat:** the §465-before-§469 ordering is
sourced to **Pub 925 (2025) / Treas. Reg. §1.469-2T(d)(6)** — NOT to an explicit sentence in the Form
6198 instructions (couldn't be located there). Cite the reg/Pub, not i6198. — *Source: 26 U.S.C.
§465(b)(1),(2),(6); Pub 925 (2025); Reg. §1.469-2T(d)(6); §461(l)(6) for the §469→§461(l) order.*

### R5 — §461(l) Excess Business Loss · **IRC §461(l) + Rev. Proc. 2024-40 + Form 461 (2025)**
- **2025 thresholds: $313,000 (single) / $626,000 (MFJ).** Rev. Proc. 2024-40 (2025 inflation adj. of the
  §461(l)(3)(A)(ii)(II) base $250k/$500k); **independently confirmed by the 2025 Form 461 instructions**
  (verbatim). (2024 was $305k/$610k — increase confirmed, not assumed.)
- **Mechanic (§461(l)(3)):** EBL = aggregate business deductions − (aggregate business gross income/gains +
  threshold).
- **Post-OBBBA (P.L. 119-21):** §461(l) is now **PERMANENT** — OBBBA removed the post-2028 sunset (Form 461
  2025 instructions state this verbatim). **Carryforward = NOL conversion** (§461(l)(2)): disallowed EBL
  becomes an NOL carryover under §172 (80%-of-taxable-income limited). ⚠ **Year-keyed flag:** the
  "**retest as a current-year business loss**" alternative was a **non-enacted proposal** — the enacted
  TY2025 law keeps NOL conversion. Re-verify each season (was actively debated).
- **Scope:** individual level, **after §469 and §465** (§461(l)(6)); partner/S-shareholder allocable share
  (§461(l)(4)); **does NOT apply to C corporations** (§461(l)(1)). — *Source: 26 U.S.C. §461(l)(1)-(6);
  Rev. Proc. 2024-40; IRS Instructions for Form 461 (2025).*

---

## Pending Gate-1 scope decisions (WO-03 initial lean in brackets)
1. **R1 self-rental + R2 PTP** — compute as one 8582 unit? [WO-03: "one 8582 authoring unit" → compute]
2. **R3 REP** — checkbox-level qualification + aggregation-election flag, or computed two-test qualification?
   [WO-03: "REP checkbox" → lighter]
3. **R4 at-risk** — diagnostic-only (route to 6198), or compute the limitation? [WO-03: "at-risk diagnostic"]
4. **R5 §461(l)** — diagnostic-only (flag over-threshold, pin $313k/$626k), or full EBL compute + NOL
   carryover? [WO-03: "§461(l) diagnostic (pin thresholds from source)"]

*Status: GAP-CHECKED → DRAFTING (brief done) → AWAITING KEN (scope walk). Nothing seeds until Gate 1.*
