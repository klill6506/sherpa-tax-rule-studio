# Form 5227 Module (WO-10) — Source Brief

*Greenfield RS-first authoring brief for Form 5227 (Split-Interest Trust Information Return).
Spun off from the 1041 module (S-11 / D-10). Opened 2026-07-05. Front-door step: GAP-CHECKED →
research-verified (this file) → Gate-1 scope walk → author.*

**Every fact below verified VERBATIM against FINAL sources by three research passes (never memory),
per the Authoritative-Source Rule.**

---

## Authoritative sources (all FINAL 2025 unless noted)

| Source | Scope | Rev/date |
|---|---|---|
| **Form 5227 (2025)**, Cat. 13227T | The split-interest information return, Parts I–IX + Schedule A | Created 5/7/25 |
| **i5227 (2025)**, Cat. 13228E | Instructions for Form 5227 | Dec 3, 2025 |
| **IRC §664** | CRT definition, §664(b) four tiers, §664(c) exemption + UBTI excise, §664(d) CRAT/CRUT quals | Cornell LII |
| **Treas. Reg. §1.664-1(d)(1)** | Category/class character ordering, within-tier rate groups, netting | Cornell LII / GovInfo |
| **IRC §642(c)** | Charitable deduction (paid vs set-aside); §642(c)(5) PIF; §642(c)(3) PIF LTCG set-aside | Cornell LII |
| **IRC §4947** | §4947(a)(2) split-interest trust; PF excise taxes; §4947(b)(3) carve-out | Cornell LII |
| **IRC §170(f)(2)** | Remainder-interest deduction (PIF); guaranteed-annuity/unitrust CLT deduction | Cornell LII |
| **Rev. Rul. 77-374 / Rev. Proc. 2016-42** | CRAT 5% probability-of-exhaustion test + sample early-termination safe harbor | IRS |
| **Form 1041-A (Rev. 9-2018)** | §6034 return for NON-split-interest §642(c) trusts (5227 family is carved out) | Sept 2018 |

> **Layout caution (research caught this):** the old Part IV-A/IV-B/V-A/V-B layout is STALE. The 2025
> Form 5227 is flat **Part I–IX** (public) + a separate **Schedule A Parts I–V** (NOT public).

---

## Who files (entity types — Form 5227 Item C)
All members of the §4947(a)(2) split-interest family file Form 5227 (it **replaces Form 1041-A** for them):
1. **Charitable lead trust (CLT)** — grantor (up-front §170(f)(2)(B) deduction) or non-grantor (annual §642(c); **also files Form 1041**).
2. **CRAT** — charitable remainder annuity trust, §664(d)(1).
3. **CRUT** — charitable remainder unitrust, §664(d)(2) (incl. NICRUT/NIMCRUT §664(d)(3) / flip variants).
4. **Pooled income fund (PIF)** — §642(c)(5) (does NOT complete Form 1041 Sch A/B; attaches a statement).
5. **Other §4947(a)(2)** — attach explanation.

**A CRT is income-tax EXEMPT (§664(c)(1))** — Form 5227 is its return; it files Form 1041 only in a UBTI year.
Due date April 15, 2026 (calendar-year); mandatory e-file; Form 8868 extension. **1041-A and 5227 are mutually exclusive.**

---

## Part structure (2025, verbatim)
| Part | Title |
|---|---|
| **Part I** | Income and Deductions — §A Ordinary (L1–8) · §B Capital gains (L9–13: ST/LT/§1250/28%) · §C Nontaxable (L14–16) · §D Deductions (L17–23, L23 = §642(c) charitable) · §E Deductions allocable to categories (§664 trust only) |
| **Part II** | Schedule of Distributable Income (**§664 trust only**) — running undistributed balances by category (ordinary/capgain/nontaxable) |
| **Part III** | Distributions of Principal for Charitable Purposes (§B tracks §642(c) set-aside carryover) |
| **Part IV** | Balance Sheet |
| **Part V** | CRAT Information · **Part VI** CRUT Information |
| **Part VII** | Statements Regarding Activities |
| **Part VIII** | Statements re Activities for which **Form 4720** may be required — L7 = §664(c)(2) UBTI; §4941/4943/4944/4945 screening |
| **Part IX** | Questionnaire for CLT / PIF / CRT |
| **Schedule A** (NOT public) | I Accumulation Schedule · II Simplified NII Calc (SNIIC) · III **Current Distributions Schedule (the FOUR-TIER)** · IV Current Distributions (CLT/PIF) · V Assets & Donor Info |

**The four-tier character engine lives on Schedule A Part III** — columns (d) Ordinary · (e) ST cap gain · (f) LT cap gain · (g) Nontaxable · **(h) Corpus** · (i) total · (j) NII.

---

## The §664(b) four-tier character-ordering engine (the compute heart)

**Tiers, worst-first / highest-tax-first (§664(b)(1)–(4), verbatim):** a CRT distribution carries out, in order,
(1) **ordinary income** (current + undistributed prior years) → (2) **capital gain** (current + undistributed) →
(3) **other income** (tax-exempt, current + undistributed) → (4) **corpus** (nontaxable return of principal).
Each tier is exhausted (current + accumulated) before the next.

**Within-tier ordering — Reg §1.664-1(d)(1) (verbatim):** within a category, distribute "from each class, in turn,
until exhaustion of the class, beginning with the class subject to the highest Federal income tax rate and ending
with the lowest." So within **Tier 2 capital gain**: ST (ordinary-rate) → 28% class (collectibles/§1202) →
unrecaptured §1250 (25%) → regular LT (20/15/0), **last**. **Order by RATE — do NOT hardcode the numeric rates**
(the reg keys off "the Federal income tax rate applicable" in the distribution year).

**Category-isolation netting (i5227, verbatim):** "A loss in any one of the three categories may not be used to
reduce a gain in any other category… However, a loss in any one category may be used to reduce undistributed gain
for earlier years within that same category, and any excess may be carried forward to reduce gain in future years
within that same category." Corpus (Tier 4) is NOT a Part II line — it is the residual via the balance sheet.

**Year-to-year accumulation (Part II):** beginning undistributed by category + current-year net (Part I §E lines)
− distributions = carryforward. This is what makes 5227 stateful.

---

## CRT qualification (established at funding; annual re-check via diagnostics)
- **CRAT §664(d)(1):** fixed annuity **5%–50%** of initial net FMV; **10% minimum remainder** (§7520 value);
  **5% probability-of-exhaustion test** (Rev. Rul. 77-374; §7520 assumed return + 2000CM mortality) — fail = no
  deduction / not qualified; **Rev. Proc. 2016-42 safe harbor** (sample early-termination provision exempts the POE test).
- **CRUT §664(d)(2):** unitrust **5%–50%** of annually-valued net FMV; **10% minimum remainder per contribution**;
  NICRUT / NIMCRUT (§664(d)(3) make-up) / flip variants.
- **§7520 rate** drives remainder valuation (higher rate → higher remainder, lower exhaustion probability).

## PIF / CLT / §4947 (non-CRT family)
- **PIF §642(c)(5):** commingled, charity-maintained, remainder to a §170(b)(1)(A) charity; income-interest valued
  at the **highest rate of return of the prior 3 years** (§1.642(c)-6 tables if <3 yrs); §642(c)(3) LTCG set-aside
  deduction. Does NOT use Part II (that's §664-trust-only).
- **CLT:** grantor (up-front §170(f)(2)(B) deduction, §671 owner, no second deduction §170(f)(2)(C)) vs non-grantor
  (annual §642(c) deduction, **also files Form 1041** as a complex trust). Never files 1041-A.
- **§4947(a)(2):** treated as a private foundation for §4941 (self-dealing) / §4943 (excess business holdings) /
  §4944 (jeopardy) / §4945 (taxable expenditures) — NOT §4940. §4947(b)(3) carves §4943/4944 for certain
  all-income-charitable trusts. Screened on Part VIII → Form 4720 if triggered.
- **§642(c) deduction:** "paid" (§642(c)(1), all) vs "permanently set aside" (§642(c)(2), **estates + grandfathered
  pre-10/9/1969 trusts only**); governing-instrument requirement; prior-year payment election.

## §664(c)(2) UBTI excise tax (year-keyed — verify)
Post-2006: a CRT with any UBTI (§512) owes a **100% excise tax on the UBTI** (§664(c)(2), Chapter 42) but **keeps
its exemption** — this is NOT the pre-2007 total-loss-of-exemption rule. Reported: Part VIII L7 = "Yes" → **Form 4720**.

---

## Open flags carried into authoring (re-verify before deep compute)
- **[year-keyed]** §664(c)(2) post-2006 100% UBTI excise (keeps exemption) — encode the post-2006 rule for TY2025.
- **[proposed reg]** Schedule A Part II SNIIC election is under **Prop. Reg. §1.1411-3(d)(3)** — NOT final; do not build compute on it.
- **[UNVERIFIED verbatim]** the full §1.664-1(d)(1)(iv) netting clause; §642(c)(2) estate-vs-trust grandfather text;
  §4947(b)(3) 60% threshold; §642(c)(3) PIF LTCG set-aside; the §4947(a)(2) exact applicable-sections list.
  Pull these verbatim before encoding the corresponding compute leg.
- **[UNVERIFIED]** the "CRT files Form 1041 in a UBTI year" leg — confirm vs §664(c)(1)/Reg §1.664-1(c).
- Re-verify all against a fresh TY2026 form (mortality table 2000CM, §7520 rate monthly).

---

## Gate-1 scope — LOCKED 2026-07-05 (DECISIONS D-11)
1. **Entity types:** CRAT + CRUT COMPUTE the §664(b) tier engine; PIF/CLT/other §4947(a)(2) = structure + diagnostics.
2. **Four-tier engine = TIER-LEVEL:** four tiers (ordinary→capgain→other→corpus) + accumulation carryforward +
   category-isolation netting; **capital gain = ONE class** (no within-Tier-2 ST/28%/§1250/regular split — deferred).
3. **CRT qualification = DIAGNOSTIC:** 5–50% payout / 10% remainder / 5% exhaustion flagged, cited; NO §7520/2000CM compute (funding-time).
4. **UBTI + §4947 = COMPUTE the excise, screen the rest:** §664(c)(2) 100% UBTI excise (year-keyed post-2006) +
   Form 4720 route; Part VIII §4941/4943/4944/4945 = screening diagnostics.

**Defaults:** one consolidated `5227` form (Parts I–IX + Schedule A structure); SNIIC deferred (proposed reg);
re-pull the [UNVERIFIED] verbatim clauses before any deeper compute leg.

## Authoring leg
- **`5227`** — `load_5227.py`: Part I income categories → Part II accumulation (tier balances) → Schedule A Part III
  four-tier distribution character → §664(c)(2) UBTI excise (Part VIII/4720). CRAT/CRUT compute; PIF/CLT/§4947 structure.
  Author `READY_TO_SEED=False` → SQLite-validate → Ken review walk → seed → export = 200.
