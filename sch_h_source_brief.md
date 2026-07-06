# Source Brief — Schedule H (Form 1040), Household Employment Taxes (TY2025)

**WO-15 · SPINE S-16 (2nd item after 8990) · greenfield RS-first**
Research pass 2026-07-05, verbatim vs FINAL 2025 IRS sources. Nothing carried [UNVERIFIED].

---

## Sources (all FINAL, posted)

| source_code | title | citation |
|---|---|---|
| `IRS_2025_SCHH` | 2025 Schedule H (Form 1040) — Household Employment Taxes | Schedule H (Form 1040) 2025, Cat. No. 12187K, **Created 4/15/25**, Attach. Seq. No. 44 |
| `IRS_2025_ISCHH` | 2025 Instructions for Schedule H (Form 1040) | Instructions for Schedule H (Form 1040), 2025 |
| `IRS_PUB926_2025` | Pub. 926 — Household Employer's Tax Guide (2025) | IRS Pub. 926 (2025) |
| `FR_FUTA_CR_2025` | Federal Register — FUTA Credit Reductions Applicable for 2025 | 91 FR (notice 2026-00342), **published 2026-01-12** |
| `IRC_3111_3301` | IRC §3101/§3111 (FICA), §3301 (FUTA), §3401 (withholding), §3510 (Sch H) | 26 U.S.C. §3101, §3111, §3301, §3306, §3510 |

---

## The form face (verbatim line map)

**Gating questions (page 1) — the who-must-file routing:**
- **Line A** — Paid any one household employee cash wages of **$2,800 or more** in 2025? *(exclude spouse, your child under 21, your parent, anyone under 18 whose principal occupation isn't household work — see below.)* → Yes: skip B/C → line 1.
- **Line B** — Withheld federal income tax during 2025 for any household employee? → Yes: skip C → line 7.
- **Line C** — Paid total cash wages of **$1,000 or more in any calendar quarter of 2024 or 2025** to all household employees? → No: **Stop, don't file.** Yes: skip 1–9 → line 10.

**Part I — Social Security, Medicare, and Federal Income Taxes:**
- L1 cash wages subject to SS tax · **L2 = L1 × 12.4% (0.124)**
- L3 cash wages subject to Medicare tax · **L4 = L3 × 2.9% (0.029)**
- L5 cash wages subject to Additional Medicare Tax withholding · **L6 = L5 × 0.9% (0.009)**
- L7 federal income tax withheld, if any (voluntary — only on employee W-4 request)
- **L8 = L2 + L4 + L6 + L7** (total SS/Medicare/FIT)
- L9 — the FUTA gate (same question as line C). No → **Stop, put L8 on Schedule 2 line 9.** Yes → line 10.

**Part II — Federal Unemployment (FUTA) Tax:**
Three qualifiers — **ALL "Yes" → Section A; ANY "No" → Section B**:
- L10 contributions to only ONE state? *(credit-reduction-state employer must check No)*
- L11 all 2025 state contributions paid by **April 15, 2026**?
- L12 all FUTA-taxable wages also taxable for state unemployment?

*Section A (simplified):* L13 state name · L14 state contributions paid · L15 cash wages subject to FUTA · **L16 = L15 × 0.6% (0.006)** → line 25.

*Section B (multi-state / credit-reduction / late):* L17 per-state table cols (a)–(h): (b) state taxable wages, (d) state experience rate, **(e) = (b) × 0.054**, (f) = (b) × (d), (g) = (e) − (f) floored at 0, (h) contributions paid · L18 totals · **L19 = col(g)+col(h) of L18** · L20 cash wages subject to FUTA · **L21 = L20 × 6.0%** · **L22 = L20 × 5.4%** · **L23 = smaller of L19 or L22** · **L24 = L21 − L23** → line 25.

**Part III — Total Household Employment Taxes:**
- L25 = amount from L8 (if line C "Yes", enter -0-) · **L26 = L16 (or L24) + L25** · L27 required to file 1040? Yes → **L26 to Schedule 2 line 9**, skip Part IV. No → complete Part IV.

**Part IV — Address & Signature** (standalone filers not filing 1040/1040-SR/1040-SS/1040-NR/1041 only).

---

## Verified 2025 constants (year-keyed — re-verify each season)

| item | 2025 value | note |
|---|---|---|
| Cash-wage SS/Medicare trigger | **$2,800** | ▲ from $2,700 (2024); indexed. **The load-bearing constant** — training data says $2,700, WRONG for 2025. |
| SS rate (combined) | **12.4%** | 6.2% ee + 6.2% er; household employer owes both halves |
| SS wage base ceiling | **$176,100** | ▲ from $168,600; per-employee cap on L1 |
| Medicare rate (combined) | **2.9%** | no wage cap |
| Additional Medicare Tax | **0.9%** over **$200,000** | employee-only portion; L5/L6 |
| FUTA quarterly test | **$1,000+ any quarter** (2024 or 2025) | lines C/9 |
| FUTA gross / max credit / net | **6.0% / 5.4% / 0.6%** | L21 / L22,L16 / L16 |
| FUTA wage base | **$7,000** per employee | — |
| **2025 credit-reduction states** | **CA 1.2% (0.012)**, **VI 4.5% (0.045)** | Fed. Reg. 2026-00342 (2026-01-12). CA eff. FUTA 1.8%, VI 5.1%. **Year-keyed — most-likely-to-change item.** |

---

## Household-employee scope (drives the gating tests + diagnostics)

- **Common-law test:** you control what work is done and how → employee (nanny, housekeeper, caregiver, private nurse, driver, yard worker). Worker controls the how → independent contractor (not Sch H).
- **Wages EXCLUDED from the $2,800 test:** your **spouse**; your **child under 21**; your **parent** (with narrow exceptions — parent IS counted when caring for your child under 18 / disabled dependent while you're widowed/divorced or spouse is disabled); an **employee under 18** at any time in 2025 whose **principal occupation is not household work** (e.g., a student).
- **EIN required** (not SSN) to report; header has both fields.

---

## 2025 law changes (OBBBA / P.L. 119-21)

**OBBBA did NOT change Schedule H's structure, rates, line layout, or math for TY2025.** Only indexed dollars moved ($2,800 trigger, $176,100 SS base) plus the annual CA/VI credit-reduction list. Qualified transportation exclusion = $325/mo; bicycle-commuting reimbursement exclusion permanently eliminated for years after 2025. The OBBBA "no tax on overtime" deduction ($12,500 / $25,000 MFJ) is a payee-side item referenced in withholding guidance — **no Schedule H line**. Nothing to encode on Sch H beyond the year-keyed constants.

---

## Proposed scope for the Gate-1 walk (compute vs defer)

1. **Part II FUTA depth** — compute Section A (0.6%) + the year-keyed credit-reduction path (CA/VI); direct-entry the full multi-state per-state experience-rate table (needs per-state SUTA data).
2. **Household-employee exclusions / gating** — compute the line A/B/C routing + $2,800 / $1,000 tests from direct-entered qualifying wages; surface exclusions (spouse/child<21/parent/under-18) as diagnostics.
3. **Part I** — compute in full (SS 12.4%, Medicare 2.9%, Add'l Medicare 0.9% over $200k, FIT withheld); diagnostic if L1 per-employee > $176,100 SS base.
4. **Filing path / entity types** — one `SCHEDULE_H` form; total → Schedule 2 line 9; standalone Part IV path + EIN requirement as diagnostics. entity_types = ? (1040 only vs 1040 + 1041).
