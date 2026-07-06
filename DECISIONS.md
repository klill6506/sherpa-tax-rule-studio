---
type: project-decisions
project: sherpa-tax-rule-studio
last_updated: 2026-07-04
---

# DECISIONS — sherpa-tax-rule-studio

*Architectural and scope choices. Append-only log. Each entry is a decision that shouldn't be re-litigated without new information. If you find yourself reopening a decision, either add a new entry that overrides the old (and say why) or leave both so the history is visible.*

---

## How to use this file

Each decision gets a dated entry with: what was decided, why, what was considered instead, and what would change our mind. Never delete entries — if a decision is reversed, add a new one that supersedes it.

---

## 2026-07-06 — D-19: Form 4952 (WO-17) v1 scope LOCKED — Investment Interest Expense Deduction

**Decision:** Per Ken's 2026-07-06 Gate-1 scope walk (4 AskUserQuestion, all recommended), Form 4952 (4th item in
the SPINE S-16 federal-forms queue, after 8990 + Schedule H + 4684):
- **(Q1) 4g election = compute the mechanic + rate-tradeoff diagnostic.** Compute the election (L4h includes the
  direct-entered elected amount, capped at 4b + 4e, default ordering 4e-then-4b) + a diagnostic on the trade-off
  (elected qualified dividends / net capital gain are taxed at ordinary rates, NOT the preferential QD/cap-gain rate)
  and the Schedule D Tax Worksheet coordination. The elected amount stays a preparer choice (direct-entry) — solving
  the optimal election is a bracket-dependent planning decision, out of scope.
- **(Q2) One `4952` form, entity_types = ['1040','1041'].** Route L8 → **Schedule A line 9** (individual) / **Form
  1041 line 10** (estate/trust); the "not required to file 4952" 3-condition exception = diagnostic.
- **(Q3) L5 misc-itemized diagnostic + investment-interest exclusion diagnostic.** L5 captures only non-miscellaneous
  items (depreciation/depletion) — a diagnostic notes 2%-floor misc itemized deductions are excluded (TCJA-suspended
  through 2025, OBBBA §67(g)-permanent); a second diagnostic lists the investment-interest exclusions (qualified-
  residence §163(h) / passive §469 → Form 8582 / tax-exempt §265 / §264 insurance / §263A capitalized).
- **(Q4) Compute full Parts I–III + indefinite carryforward.** L3 = L1 + L2; L4c = 4a−4b; L4f = 4d−4e; L4h =
  4c+4f+4g; L6 = max(0, L4h−L5); **§163(d) limitation L8 = min(L3, L6)**; **L7 = max(0, L3−L6) carries forward
  INDEFINITELY** (§163(d)(2); L2 pulls the prior-year L7).

**Context:** WO-17 front door: gap-check (GAP — `lookup/4952/export/` = 404; downstream Sch A / Sch D / QDCGT route
TO 4952 but none authors it) → verbatim research pass (FINAL 2025 Form 4952 Created 5/28/25; **no separate i4952 —
instructions on pp. 3-4 of the form PDF** + §163(d)) → `f4952_source_brief.md` → this walk. **§163(d) is UNCHANGED by
OBBBA for TY2025** (no "What's New" on the form); OBBBA's interest changes are §163(j) **business** interest (Form
8990) — a different provision, not conflated. The only adjacent OBBBA item is §67(g) misc-itemized permanence (affects
the L5 exclusion, already true for 2025).

**Alternatives considered:** solve the optimal 4g election (rejected — bracket-dependent planning, not a spec
compute); 4g direct-entry with no diagnostic (rejected — the rate trade-off is the whole point of the election);
entity_types 1040-only (rejected — trusts commonly carry investment interest, ties into the 1041 module); L7
carryforward as direct-entry (rejected — the indefinite roll is the §163(d)(2) mechanic worth asserting).

**Would reconsider if:** the forms-usage report shows heavy 4g-election activity (build the optimization); the 2026
form changes the L5 misc-itemized wording (OBBBA made the suspension permanent — watch the language, no compute change).

**Year-keyed / re-verify at TY2026:** none dollar-valued; watch the L5 misc-itemized-deduction wording on the 2026
form (the exclusion is now permanent) and re-confirm §163(d) is still un-amended.

---

## 2026-07-05 — D-18: Form 4684 (WO-16) v1 scope LOCKED — Casualties and Thefts

**Decision:** Per Ken's 2026-07-05 Gate-1 scope walk (4 AskUserQuestion, all recommended), Form 4684 (3rd item in
the SPINE S-16 federal-forms queue, after 8990 + Schedule H):
- **(Q1) Section A (personal) = full compute incl. the qualified-disaster path.** Per-property loss = min(adjusted
  basis, FMV decline) − insurance; the **$100 floor** (L11); the **§165(h)(5) federally-declared-disaster
  limitation** gate (a personal loss is deductible ONLY if attributable to a federally declared disaster, except to
  the extent of personal casualty gains); the **10%-of-AGI floor** (L17); AND the **qualified-disaster special path**
  ($500 floor, NO 10%-AGI, add-to-standard-deduction) with the OBBBA-extended declaration window (declared 1/1/2020 –
  **9/2/2025**, incident began by 7/4/2025, ended by 8/3/2025) in a year-keyed dict.
- **(Q2) Section B (business/income-producing) = Part I + Part II §1231 netting + route.** Compute Part I per-property
  loss/gain (total destruction / theft → full basis, ignore FMV); Part II holding-period split: **≤1 yr → ordinary
  (Form 4797 line 14)**; **>1 yr losses>gains → ordinary (4797 L14)**; **>1 yr gains≥losses → §1231 capital (4797 L3)**.
  Direct-entry the 4797/Schedule D linkage via flow assertions.
- **(Q3) Section C compute, Section D diagnostic.** COMPUTE Section C Ponzi-type theft safe harbor (Rev. Proc.
  2009-20: qualified investment × **95%** no-recovery / **75%** potential-recovery − recoveries → Section B). Section D
  **§165(i)** election to deduct a disaster loss in the preceding year = structure + diagnostic (filing-mechanics, not
  a compute).
- **(Q4) One `4684` form, entity_types = ['1040','1065','1120S','1120'].** Serves Section A personal (1040) + Section B
  business casualty (all entities; partnerships → 1065 Sch K L11, S-corps → 1120-S Sch K L10). Model the **new OBBBA
  financial-scam theft loss** as a Section B diagnostic (3 conditions: criminal theft under state law / no reasonable
  prospect of recovery / transaction entered into for profit — NOT subject to the FDD limitation).

**Context:** WO-16 front door: gap-check (GAP — `lookup/4684/export/` = 404; downstream Sch A/Sch D/4797/8829 route
TO 4684 but none authors it) → verbatim research pass (FINAL 2025 Form 4684 Created 9/26/25 + i4684 updated 30-Apr-2026
+ Pub 547 + §165 + Rev. Proc. 2009-20) → `f4684_source_brief.md` → this walk. **Load-bearing law finding: the
§165(h)(5) FDD-only limitation is STILL in effect for TY2025; OBBBA EXTENDED the qualified-disaster special rules
(window to 9/2/2025) and ADDED the financial-scam theft-loss avenue — it did NOT repeal the base limitation or add
state-declared disasters.**

**Alternatives considered:** qualified-disaster path as diagnostic-only (rejected — the $500/no-AGI/standard-deduction
package is season-critical and computable); Section B Part I only, Part II direct-entry (rejected — the §1231 holding-
period split is the routing that makes the 4797 handoff correct); Sections C & D both diagnostic-only (rejected —
the Ponzi 95%/75% safe harbor is a clean compute; but Section D election IS left as diagnostic, low frequency);
entity_types 1040-only (rejected — Section B serves business property of any entity, matching 4562/4797/3800).

**Would reconsider if:** the forms-usage report shows Ponzi/§165(i)/financial-scam volume warrants deeper compute;
the within-Section-B employee-property line (post-TCJA generally nondeductible) needs its own gate.

**Year-keyed / re-verify at TY2026:** the qualified-disaster declaration window (1/1/2020 – 9/2/2025, OBBBA-set — the
most-likely-to-churn item), the $100/$500 floors, the 10%-AGI floor, and the 95%/75% Ponzi factors.

---

## 2026-07-05 — D-17: Schedule H (WO-15) v1 scope LOCKED — Household Employment Taxes

**Decision:** Per Ken's 2026-07-05 Gate-1 scope walk (4 AskUserQuestion, all recommended), Schedule H (Form 1040)
(2nd item in the SPINE S-16 federal-forms queue, after 8990):
- **(Q1) FUTA = Section A + the credit-reduction path.** COMPUTE Section A (L16 = FUTA wages × 0.6%) AND the
  single-state credit-reduction case via a year-keyed rate dict (**2025: CA 1.2% / VI 4.5%**, Fed. Reg. 2026-00342);
  net FUTA for a timely single credit-reduction state = FUTA wages × (0.6% + reduction rate) = the L21 − L23
  mechanic. DIRECT-ENTRY the full multi-state per-state experience-rate table (L17 cols a–h, L19) since per-state
  SUTA experience rates are data the spec can't reach; L24 = L21 − L23 computed from the direct-entered L19.
- **(Q2) Gating tests from qualifying wages + exclusion diagnostics.** COMPUTE the line A/B/C who-must-file routing
  and the **$2,800** (any one employee) / **$1,000-per-quarter** (all employees) tests from direct-entered
  QUALIFYING cash wages; surface the four exclusions (spouse / child under 21 / parent-with-exceptions /
  under-18-not-principal-occupation) as diagnostics — the relationship/age determination needs data the spec can't read.
- **(Q3) One `SCHEDULE_H` form, entity_types = ['1040'].** Total → Schedule 2 (Form 1040) line 9. Standalone-filer
  **Part IV** path (line 27 "No") + the **EIN-required** rule = diagnostics. The 1041-attached estate/household-employer
  case is noted but not a separate entity type (household employers are overwhelmingly individuals).
- **(Q4) Full Part I compute + SS-base diagnostic.** COMPUTE L2 (SS 12.4%), L4 (Medicare 2.9%), L6 (Additional
  Medicare 0.9% over $200,000), L7 FIT withheld, L8 total; diagnostic when L1 per-employee SS wages exceed the
  **$176,100** 2025 SS wage base (year-keyed).

**Context:** WO-15 front door: gap-check (GAP — no loader, not in the 111-form prod set) → verbatim research pass
(FINAL 2025 Schedule H Created 4/15/25 + i-Sch-H + Pub 926 + Fed. Reg. FUTA-credit-reduction notice) →
`sch_h_source_brief.md` → this walk. **Research CAUGHT the load-bearing correction: the 2025 cash-wage trigger is
$2,800, NOT the $2,700 training-data/2024 figure.** OBBBA did NOT change Schedule H structure/rates/layout for
TY2025 — only indexed dollars ($2,800 trigger, $176,100 SS base) and the annual CA/VI credit-reduction list moved.

**Alternatives considered:** full Section B multi-state worksheet compute (rejected — per-state experience rates are
preparer data; the credit-reduction single-state case is the common one and is the year-sensitive risk); encode the
exclusion determination from structured relationship/age facts (rejected — needs per-employee data the spec can't
read; diagnostic is the honest surface); entity_types 1040+1041 (rejected — estate household employers are rare;
noted, not modeled); Section-A-only defer Section B (rejected — the CA/VI credit reduction is a live 2025 item).

**Would reconsider if:** the forms-usage report shows multi-state household employers are common (build the full L17
table); the credit-reduction state list changes for TY2026 (year-keyed dict forces re-verify); the 1041 household-
employer case shows up (add the entity type + 1041 routing).

**Year-keyed / re-verify at TY2026:** $2,800 trigger, $176,100 SS base, $200,000 Add'l-Medicare threshold, $7,000
FUTA base, and ESPECIALLY the credit-reduction state list (CA/VI for 2025 — the most-likely-to-change item).

---

## 2026-07-05 — D-16: Form 8990 (WO-14) v1 scope LOCKED — §163(j) business-interest limitation

**Decision:** Per Ken's 2026-07-05 Gate-1 scope walk (3 AskUserQuestion, all recommended), Form 8990 (first of
the SPINE S-16 federal-forms queue; finishes the 1120 module's §163(j) deferred leg):
- **(Q1) Full compute Part I.** ATI (tentative taxable income + additions incl. the **L11 EBITDA add-back** for
  dep/amort/depletion, OBBBA-restored for TY2025 − reductions) → 30% × ATI (L26) → total limitation L29 (30% ATI +
  BII + floor plan) → allowable BIE L30 = min(total BIE, limit) → disallowed-BIE carryforward L31 (indefinite).
- **(Q2) Compute Part II/III formulas, direct-entry Sch A/B.** Partnership EBIE (L32), ETI (L36 = ratio × ATI),
  excess BII (L37); S-corp ETI (L41), excess BII (L42, no EBIE). Per-owner Schedule A/B allocation = direct-entry.
- **(Q3) Compute the $31M gate + diagnose excepted businesses.** §448(c) small-business exemption (avg gross
  receipts ≤ $31M, non-tax-shelter → not required to file); §163(j)(7) excepted trades/businesses (electing
  real-property/farming, regulated utilities, employee services) = diagnostic (elect out of the limit).

**Context:** entity_types = 1120/1065/1120S/1040. Verified vs FINAL Form 8990 Rev. 12-2025 + i8990 + §163(j). The
L11 EBITDA add-back is the load-bearing item (was suspended 2022-24, reinstated by OBBBA). Cite the effective date
to P.L. 119-21 + i8990 (Cornell §163(j)(8) lags). One consolidated `8990` form.

**Would reconsider if:** the per-partner Schedule A allocation (EBIE by partner) proves common enough to compute;
TY2026 changes the $31M index or the electively-capitalized-interest character rule (OBBBA, years after 12/31/2025).

---

## 2026-07-05 — D-15: NC + AL pass-through batch (WO-13) v1 scope LOCKED — D-403/CD-401S + Form 65/20S

**Decision:** Per Ken's 2026-07-05 Gate-1 scope walk (4 AskUserQuestion, all recommended), the NC + AL
pass-through entity batch (completes the adjacent-state pass-through track; SC done via SC1065/SC1120S/PTET, D-9):
- **(Q1) Full compute both states.** COMPUTE both entity-level PTETs — **NC Taxed PTE 4.25%** (individual rate)
  / **AL Electing PTE 5%** (Form EPT) — plus the companions: NC franchise on CD-401S ($1.50/$1,000, $500 first-$1M
  cap, $200 min, reuse the CD-405 `_nc_franchise` helper), NC nonresident withholding 4.25%, AL composite PTE-C 5%.
  Depreciation: NC decouple (85% bonus + §179 $25k/$200k); AL conforms (no add-back).
- **(Q2) Encode NC deduction + AL credit** (the owner-side SALT-cap benefit, which DIFFERS): NC owner DEDUCTS their
  share of Taxed-PTE income (removed from NC AGI via NC-PE); AL owner takes a REFUNDABLE CREDIT for their share of
  the EPT paid (Schedule EPT-C). Each modeled + diagnostic.
- **(Q3) AL Form 20S non-electing entity taxes = diagnostic + direct-entry** (Line 32 = LIFO recapture §40-18-161 /
  built-in gains §40-18-174 / excess net passive income §40-18-175 — the federal S-corp-level taxes; not recomputed).
- **(Q4) 2 loaders, state-paired:** `load_nc_passthrough.py` (NC_D403 + NC_CD401S), `load_al_passthrough.py`
  (AL_FORM_65 + AL_FORM_20S) — mirroring `load_sc_passthrough.py`. AL Form EPT = a compute node referenced from the
  65/20S Sch K lines (not its own form).

**Context — the PTET contrast is the headline (verify per state, never clone GA):** NC 4.25% / owner deduction vs
AL 5% / owner refundable credit. Research corrections: AL election = checkbox on Form 65/20S + Form EPT (NOT the old
PTE-E/MAT); CD-401S DOES compute NC franchise on S-corps; AL conforms to §168(k)/§179 (item-by-item, not blanket).

**Reuse:** NC re-declares CD-405's bonus/§179/franchise sources; AL re-declares 20C's conformity sources.

**Alternatives considered:** AL_FORM_EPT as its own form (rejected — referenced compute node is lighter, matches the
65/20S Sch K reference); compute the AL LIFO/BIG/excess-passive (rejected — niche federal-level taxes); entity-only
PTET without the owner side (rejected — the owner deduction/credit is the SALT-cap point and differs by state).

**Would reconsider if:** NC/AL rates change on their phase tracks; NC adds a franchise on partnerships (currently
S-corp only); the owner-side flow needs the downstream 1040/D-400/AL-40 credit-import built.

**[UNVERIFIED] re-pull before seeding:** exact NC D-403/CD-401S/NC-PE line numbers (PDFs didn't text-extract) and
the TY2025 AL Sch K line numbers (25f65instr/25f20sinstr when posted).

---

## 2026-07-05 — D-14: State C-corp batch (WO-12) v1 scope LOCKED — SC1120 + AL 20C + NC CD-405

**Decision:** Per Ken's 2026-07-05 Gate-1 scope walk (4 AskUserQuestion, all recommended), the reuse-state
C-corp batch (extends the federal 1120 module WO-11 to GA's income-tax neighbors) is scoped:
- **(Q1) Full compute all three.** SC1120: 5% flat + §168(k) decouple / §179 $1.25M/$3.13M delta + license fee
  ($15 + capital×.001, min $25). NC CD-405: 2.25% income (S.B. 105 phase-down) + 85% bonus add-back / §179
  $25k/$200k + franchise tax ($1.50/$1,000 net worth, first-$1M cap $500, min $200, holding cap $150k). AL 20C:
  6.5% + NO depreciation add-back (AL conforms). All single-sales-factor apportionment. Federal-TI start.
- **(Q2) AL FIT deduction = compute apportioned.** federal income tax × AL apportionment ratio (Schedule E line 9),
  subtracted at L11a. NOTE the constitutional basis (Amendment 662) so it isn't "corrected" away.
- **(Q3) SC = author current law + prominent flag.** Author SC to the enacted 12/31/2024 conformity (§168(k)
  decouple, §179 $1.25M/$3.13M) with a prominent year-keyed diagnostic on the **H.3368/OBBBA live wire**
  (retroactive TY2025 risk; SCDOR extended the SC deadline to Oct 15 2026). **RE-VERIFY H.3368 before seeding SC**;
  AL/NC seed independently.
- **(Q4) AL GILTI/§174 = diagnostic + direct-entry.** Since AL conforms on depreciation, the AL-specific decouples
  are GILTI (§40-18-35.2: §951A subtract / §250 add-back) and §174 R&E (§40-18-62): model as Schedule A lines +
  diagnostics, direct-entry the amounts (no full GILTI compute).

**Context — two premises OVERTURNED by the research (Authoritative-Source Rule in action):**
(1) The AL C-corp federal income tax deduction is **NOT repealed** — it is constitutionally protected (Amendment
662) and computed on the 2025 Form 20C (L11a/Schedule E). The Act-2021-1-repeal assumption was false; both AL
Form 40 and Form 20C keep the FIT deduction. (2) The NC franchise tax base is **net-worth-only** (the "greatest of
net worth / 55% ad valorem / NC tangible investment" three-way test was repealed effective TY2017). Also: **AL
fully CONFORMS to §168(k)/§179** (rolling conformity, OBBBA flows through — the opposite of SC/NC/GA).

**Reuse:** each loader re-declares its state conformity/statute sources (by source_code, idempotent) + a new
state-form source. SC §179 $1.25M/$3.13M (as SC1040/SC1120S); NC §179 $25k/$200k + 85% add-back (as NC D-400).

**Alternatives considered:** hold SC entirely until H.3368 resolves (rejected — author + flag is lower-friction,
matches SC1040/SC1120S; re-verify gate before the SC seed); compute AL GILTI/§174 inline (rejected — low
population); structure-only companion taxes (rejected — license fee / franchise tax are core and cheap to compute).

**Would reconsider if:** H.3368 is enacted (flip SC §168(k)/§179 to OBBBA retroactively for TY2025); NC's rate
changes on the next phase-down step; AL GILTI/§174 activity proves common in the C-corp population.

---

## 2026-07-05 — D-13: 1120 C-corp module (WO-11) v1 scope LOCKED — Gate-1 walk

**Decision:** Per Ken's 2026-07-05 Gate-1 scope walk (4 AskUserQuestion, all recommended options), the
Form 1120 C-corp module v1 is scoped:
- **(Q1) Form shape = spine + 2.** Three RS forms: **`1120`** = the compute spine (page-1 income/deductions +
  Schedule C DRD + Schedule J tax computation → total tax); **`1120_SCHL`** = Schedule L balance sheet + M-1 +
  M-2 + Schedule K other-info gates; **`GA600`** = Georgia. Mirrors the 1041 consolidated-spine precedent (not
  the 1120-S full split).
- **(Q2) Schedule C DRD = domestic + §246(b) limit.** COMPUTE the domestic DRD (L1/2/8/10/11 → 50/65/100%) +
  the §246(b) taxable-income limitation with the §172 NOL loss-exception. DIAGNOSTIC/direct-entry: §246(c)
  holding period, §246A debt-financed reduction, and the foreign/GILTI/§250 lines (13/17/22).
- **(Q3) Federal = NOL compute, rest defer.** COMPUTE the §172 NOL **80%**-of-taxable-income limitation
  (page-1 L29a; available carryover direct-entry from Sch K Q12). DIAGNOSTIC/RED-defer + route: §163(j) → gate
  on Sch K Q24 (>$31M §448(c)) → Form 8990 (note OBBBA EBITDA-basis for TY2025); §55 CAMT → Form 4626
  (Sch K Q29, $1B AFSI); §541 PHC → Schedule PH; §531 AET; §1062 farmland-deferral → Form 1062.
- **(Q4) GA Form 600 = full.** COMPUTE both taxes: income tax (federal taxable income → Sch 4 additions incl.
  §168(k) bonus add-back → Sch 5 GA-depreciation subtraction → Schedule 6 single-factor gross-receipts
  apportionment, 6 decimals → **5.19%** → GA NOL 80%) AND the **net worth tax** bracket table (Schedule 2,
  ≤$100k=$0, max $5,000 over $22M). Uses the verified **GA §179 2025 = $1,250,000 / $3,130,000** delta
  (GA700/GA600S depreciation-delta pattern).

**Context:** WO-11 front door: gap-check (8 gaps; 1125-A/1125-E/3800/4562/4797/8949/7004 confirmed covering
1120) → 3 verbatim research passes → `f1120_source_brief.md` → this scope walk. Compute the headline mechanics
(21% tax, DRD, NOL 80%, GA dual tax), screen + route the low-population special regimes.

**⚠ Cross-cutting finding — GA §179 staleness.** The verified 2025 GA Form 4562 (Rev. 08/01/25) states GA §179
= **$1,250,000 / $3,130,000** for 2025 (GA indexes its §179). The **$1,050,000 / $2,620,000** in CLAUDE.md's
"Verified Rules — 2025" section is the **2021** figure and is STALE. GA600 uses the verified 2025 figure; the
existing **GA700 / GA600S** specs (STATUS notes cite $1.05M/$2.62M) should be re-checked for the same staleness
and CLAUDE.md corrected. Flagged to Ken.

**Alternatives considered:** full 1120-S-style split (rejected — the 1041 consolidated spine is cleaner for the
compute core); full Schedule C incl. §246A/foreign (rejected — low population, defer to re-verify); inline
§163(j) compute (rejected — duplicates Form 8990); GA income-tax-only (rejected — the net worth tax is core GA
C-corp compliance and cheap to table).

**Would reconsider if:** C-corp population shows heavy foreign-dividend / debt-financed-portfolio activity
(expand Sch C), frequent §163(j)-limited corporations (build the 8990 compute), or CAMT-scale clients ($1B AFSI).

---

## 2026-07-05 — D-12: 1120 C-corp module ADDED to the season-one plan (S-13 / WO-11)

**Decision:** Add the **C corporation (Form 1120)** federal module — plus its GA companion (Form 600) — to
the season-one build plan as **BUILD_ORDER S-13 / WORK_ORDERS WO-11**, greenfield RS-first. This is a scope
ADD beyond the original season-one compliance set (which was 1040 / 1120-S / 1065 / 1041 federal + GA/SC/AL/NC
states). PRODUCT_MAP compliance line updated to include 1120.

**Context:** Ken's call 2026-07-05, after the RS authoring spine came in clear (S-1..S-11 + WO-10 all DONE a
month ahead of the Sept–Oct plan). The C corporation is a **genuinely new entity type** — nothing in the
current form set computes it (1120-S is the S-corp; 4562/4797/3800 carry '1120' in entity_types for
depreciation/disposition/GBC but there is no 1120 income-tax spine). Ken intends to build it next: he will
clear context and prompt "build 1120", at which point the fresh session runs the WORK_ORDERS front door from
step 1 (gap-check → research-verify → source brief → Gate-1 scope walk → author).

**Required set (the gap-check target, BUILD_ORDER S-13):** 1120 spine (page-1 income → deductions → taxable
income → §11 flat 21% tax); Schedule C (dividends-received deduction §243/§245A); Schedule J (tax computation);
Schedule K (other info) + Schedule L (balance sheet); M-1/M-2 (book-tax reconcile + retained earnings; M-3
$10M threshold); 1125-A (COGS) + 1125-E (officer compensation); GA Form 600 (GA C-corp income + net worth
tax). Depreciation/disposition/GBC (4562/4797/3800) are expected to already cover 1120 — confirm at gap-check
(the 1065-core 8825/4562/3800 precedent). The v1 compute-vs-defer scope (NOL §172 80% limit, §163(j), the §55
corporate AMT / CAMT, PHC and accumulated-earnings taxes) is a Gate-1 scope-walk decision at build time, NOT
pre-decided here.

**Alternatives considered:** leave 1120 out of season one (rejected — the practice has C-corp clients and the
runway opened up); fold it into the adjacent-state entity track as just FL F-1120 (rejected — the federal 1120
is the core need; FL F-1120 / other state C-corp returns are companions that reuse the federal 1120 flow).

**What would change our mind:** if the TaxWise forms-usage report shows the firm's C-corp population is
negligible, the module can be deferred; if a specific C-corp complexity (consolidated returns §1501, CAMT) is
common, that expands the Gate-1 scope. CAMT (§55, 15% on $1B+ AFSI) is expected to be RED-deferred as
out-of-population, decided at the scope walk.

---

## 2026-07-05 — D-11: Form 5227 (WO-10) v1 scope — CRAT/CRUT compute the §664 tier engine (tier-level), PIF/CLT/§4947 = structure, quals = diagnostic, UBTI excise computed

**Decision:** The Form 5227 (Split-Interest Trust Information Return) v1 spec — spun off from the 1041
module (D-10) as its own greenfield order — is scoped per Ken's 2026-07-05 Gate-1 walk (4 AskUserQuestion):
- **(Q1) Entity types:** COMPUTE the §664(b) tier engine for **CRAT (§664(d)(1)) + CRUT (§664(d)(2))**;
  model **pooled income funds (§642(c)(5)), charitable lead trusts, and other §4947(a)(2)** trusts as
  STRUCTURE + diagnostics (PIF = the §642(c)(5) statement-path / no-Sch-B note; CLT = grantor vs
  non-grantor routing, non-grantor also files Form 1041; other = catch-all).
- **(Q2) Four-tier engine = TIER-LEVEL:** COMPUTE the four §664(b) tiers (ordinary → capital gain →
  other/tax-exempt → corpus, worst-first) and the year-to-year undistributed **accumulation carryforward**
  (Part II), with the **category-isolation netting** (a loss in one category cannot reduce another; carries
  within-category). Treat **capital gain as ONE class** — do NOT split within Tier 2 into the ST/28%/
  unrecaptured-§1250/regular-LT rate groups (that within-tier detail is preparer-entered). Chosen over the
  full within-tier engine to keep v1 tractable; the rate-group split is a later refinement.
- **(Q3) CRT qualification = DIAGNOSTIC:** flag the 5%–50% payout range, the 10% minimum remainder, and the
  5% probability-of-exhaustion test (Rev. Rul. 77-374; Rev. Proc. 2016-42 safe harbor) with the rule cited,
  but do NOT build the §7520 / 2000CM-mortality actuarial compute — these are established at trust FUNDING
  (and re-checked with specialized planning software), not recomputed on the annual return.
- **(Q4) UBTI + §4947 = COMPUTE the excise, screen the rest:** COMPUTE the §664(c)(2) **100% excise tax on
  any UBTI** (year-keyed **post-2006** rule: the trust KEEPS its exemption and pays 100% of UBTI as a
  Chapter 42 excise — NOT the pre-2007 total loss of exemption) and route to **Form 4720**; model Part VIII
  §4941 (self-dealing) / §4943 (excess business holdings) / §4944 (jeopardy) / §4945 (taxable expenditures)
  as screening diagnostics (→ Form 4720 if triggered; §4940 does NOT apply).

**Context:** WO-10, spun off from S-11 (D-10) because the §664 split-interest family is a distinct body of
law. All facts verified verbatim vs FINAL 2025 Form 5227 (Created 5/7/25) + i5227 (Dec 3 2025) + IRC §664/
§642(c)/§4947/§170(f)(2) + Reg §1.664-1(d)(1) — see [f5227_source_brief.md]. Form 5227 REPLACES Form 1041-A
for split-interest trusts; a CRT is income-tax exempt (§664(c)(1)) and files 5227 as its return.

**Alternatives considered:** All-types-computed (rejected — PIF §642(c)(5)/(3) valuation + CLT §170(f)(2)/
§642(c) deduction mechanics roughly double the module for low frequency). Full within-Tier-2 rate-group
engine (rejected for v1 — ST/28%/§1250/regular ordering by dynamic rate is a heavy refinement; tier-level
covers the character carry-out). Compute the qualification actuarials (rejected — §7520/mortality belongs to
funding-time planning software, not the annual information return). UBTI diagnostic-only (rejected — the
excise is literally 100% of UBTI, trivial to compute).

**What would change our mind:** if returns need the beneficiary's LT rate-group detail, add the within-Tier-2
split (Q2 upgrade). If PIF/CLT frequency warrants, compute their deduction mechanics (Q1 upgrade). Re-pull the
[UNVERIFIED] verbatim clauses (§1.664-1(d)(1)(iv) netting; §642(c)(2)/(3); §4947(b)(3) 60%) before any deeper
compute leg. The SNIIC election (Schedule A Part II) is PROPOSED reg only — do not build on it. Re-verify at TY2026.

---

## 2026-07-05 — D-10: 1041 module (S-11/WO-09) v1 scope — core 4 + ESBT computed, FULL distribution engine, cap-gains-in-DNI direct-entry, GA 501 resident-only, Form 5227 spun off as its own leg

**Decision:** The greenfield federal 1041 fiduciary module (S-11 spine → DNI/IDD/Sch B → Sch G → K-1 →
GA 501) v1 scope, locked at the 2026-07-05 Gate-1 scope walk (AskUserQuestion, 4 + 1 follow-up):
- **(Q1) Entity types:** COMPUTE the core four (decedent's estate, simple trust, complex trust, qualified
  disability trust) fully + COMPUTE the **ESBT** S-portion separate-rate worksheet (top trust rate → Sch G
  Part I line 4). Model **grantor-type trust** as structure + the grantor-letter reporting path (NO K-1,
  dollars on an attachment). **Pooled income fund** = recognized entity type, routed to the Form 5227 leg
  (below). **Bankruptcy estate (ch. 7/11)** = RED-defer diagnostic (it is essentially an individual 1040).
- **(Q2) Distribution engine = FULL:** COMPUTE the §662 two-tier allocation (first-tier line 9 / second-tier
  line 10, DNI applied tier-1-first), the §663(c) separate-share DNI, the §663(b) 65-day election (Question 6
  checkbox), and proportional character retention of each DNI class to beneficiaries. The most correct
  subchapter-J engine; the heaviest reconcile leg.
- **(Q3) Capital gains IN DNI = direct-entry + diagnostic:** preparer enters Schedule B line 3 (gains
  attributable to income / treated-as-distributed); a diagnostic surfaces the three Reg. §1.643(a)-3(b)
  circumstances so the determination is documented, not silent. Default is corpus-excluded (§643(a)(3)).
  Chosen because inclusion hinges on the governing instrument + local law + the fiduciary's reasonable
  discretion — data the spec cannot read.
- **(Q4) GA Form 501 = resident-only v1:** COMPUTE the full-year resident 501 (federal 1041 Adjusted Total
  Income line 17 → beneficiary subtraction at 501 L4 → flat **5.19%** → $1,350/$2,700 exemptions → Sch 5/6
  credits). RED-defer the Schedule 4 nonresident source allocation AND the §168(k)/§179 GA-nonconformity
  add-backs to a later leg. (Diverges from the GA-700 MAXIMAL choice — a fiduciary book skews resident, and
  GA Form 501 has no dedicated depreciation line; the add-back would ride generic Sch 2 "Other" under §48-7-27.)
- **(follow-up) Form 5227 = its own dedicated leg:** author the split-interest-trust module (PIF + charitable
  remainder CRAT/CRUT + charitable lead trusts, incl. the §664(b) four-tier character-ordering regime) as a
  SEPARATE authoring leg WITH its own focused research pass + source brief — NOT folded inline. The §664 CRT
  distribution regime is a distinct body of law that earns verbatim source verification of its own.
- **Pre-decided (not walked):** Schedule I AMT = RED-defer diagnostic (D-2, unchanged); K-1 (Form 1041) full
  verbatim code transcription of boxes 9/11/12/13/14 (the 1065-K-1 precedent); form-key consolidation =
  one **`1041`** form (page-1 + Schedule B + Schedule G, tightly coupled: L18 IDD←Sch B L15, L24 tax←Sch G L9)
  + separate **`SCHEDULE_K1_1041`** + **`GA501`**; OBBBA §1062 (Form 1062 farmland installment, L25b/Sch G 18c) =
  structure + flag, low frequency.

**Context:** BUILD_ORDER S-11, the greenfield Sept 1041 rock (~70 trust returns, Ken's specialty, Apr 15
deadline). RS-first mode: enumerate the set, gap-check, author + Gate-1-approve all gaps, THEN dispatch the
tts app build. All TY2025 constants verified verbatim against FINAL IRS/GA sources in [f1041_source_brief.md]
(2025 Form 1041 Created 10/28/25; i1041 Mar 5 2026; 2025 Sch K-1; GA Form 501 Rev. 07/09/25). Rev. Proc.
2025-32 confirmed to be the TY2026 procedure — 2024-40 governs TY2025.

**Alternatives considered:** All-9-entity-types (rejected — PIF/bankruptcy are very low frequency; PIF is
better served by the dedicated 5227 leg). Core-IDD-only distribution engine (rejected — Ken wanted the full
tier/separate-share/65-day, his specialty). Compute cap-gains-in-DNI from structured flags (rejected — bakes
in an instrument-specific judgment that could mislead). GA 501 maximal like GA-700 (rejected for v1 — fiduciary
book skews resident, no dedicated GA depreciation line). Full 5227 inline (rejected — roughly doubles the
module and mixes two regimes; gets its own leg instead).

**What would change our mind:** if the forms-usage report shows ESBT/grantor/bankruptcy or nonresident GA
trusts are common, upgrade those from defer/structure to compute. If the §663(c) separate-share or §662
multi-tier compute proves to need per-share data the spec can't reach, fall back to structured-diagnostic for
those sub-legs (a reconcile-leg call). Re-verify ALL constants at TY2026 (OBBBA §67/§68 bite for years after
12/31/2025; the 2026 breakpoints are already known — see the brief).

---

## 2026-07-05 — D-9: SC1065 + SC1120S v1 — BOTH authored; SC PTET = the §12-6-545(G) 3% ATB entity election (owner EXCLUSION, not credit); §179 = indexed $1.25M/$3.13M (Reading A)

**Decision:** Extend the GA-700 + PTET work to Georgia's neighbors (Ken: "states adjacent to
Georgia" — the individual returns AL/NC/SC are already done, so the frontier is the pass-through
*entity* returns + PTET). Ken picked **SC pass-through + PTET**; the 2026-07-05 walk (4
AskUserQuestion) locked v1 as: (Q1) **author BOTH SC1065 (partnership) and SC1120S (S-corp)** this
session in one loader (`load_sc_passthrough.py`), SC1065 being the cleaner PTET vehicle and ~80% of
its SC-K/apportionment/I-435 engine ported to SC1120S; (Q2) **COMPUTE** the §168(k) bonus add-back
structure (year-1 add-back + remaining-life SC-basis subtraction) AND the §179 conformity delta,
direct-entering the asset-level SC-4562 figures the engine can't reach (GA-700 (B) precedent — Ken
is a depreciation CPA); (Q3) the SC §179 2025 cap = the **INDEXED $1,250,000 / $3,130,000**
(Reading A: conformed IRC §179 incl. its indexing provision; Rev. Proc. 2024-40), NOT the
conservative 2024 $1,220,000/$3,050,000 — matching the SC1040 pin; (Q4) **COMPUTE** apportionment
methods 1 (sales-only, TPP dealers) & 2 (gross-receipts, service/financial) via a business-type
selector (4 decimals) + the 5% nonresident withholding with the full exemption set (residents /
I-309 / composite / 501(a) / entity-taxed ATB), **RED-defer** special/individualized apportionment
+ the composite return (I-348/I-338) + the SC1120S multi-state license-fee apportionment + Schedule
D Annual Report. Structure/constants verified against the FINAL 2025 SCDOR sources (I-435 Rev.
1/30/25; SC1065 Rev. 6/18/25; SC1120S Rev. 6/17/25; I-335 Rev. 6/17/25; SC1120I; §12-6-545) — see
[sc1065_source_brief.md].

**Context:** SC's PTET is NOT a GA-700 clone. It is the **Active Trade or Business (ATB) elective
entity-level tax** (§12-6-545(G), Act 61 of 2021), computed on **Form I-435** at a **flat 3%** on
**active trade or business income ONLY** (excludes passive/investment income, capital gains,
§707(c) service payments). The election is **annual and NON-BINDING** (contrast GA's irrevocable
5.19%), a page-1 checkbox. The owner side is an **EXCLUSION, not a credit** (§12-6-545(G)(3)): the
owner SUBTRACTS the entity-taxed amount on **I-335 line 6** (partner ← SC1065 K-1 line 14;
shareholder ← SC1120S K-1 line 13). Entity-taxed ATB is also exempt from the 5% nonresident
withholding (SC1065 L6 = L1 − L2). SC1120S additionally carries a general **5%** SC income tax on
non-ATB net (L9) and a **license fee** (capital × .001 + $15, min $25) with no partnership analog.

**Divergence from precedent (called out):** GA-700's PTET is 5.19%, irrevocable, on the entity's
whole GA taxable income, with a PTEDED/PTEADD owner subtraction/addition on Form 500. SC's is 3%,
annual/non-binding, on ATB income only, with the owner exclusion via I-335 L6. The §179 Reading-A
pin ($1.25M/$3.13M) is **not SCDOR-stated** (the booklets defer to conformed IRC §179) — cited to
Rev. Proc. 2024-40 pending SCDOR confirmation, and stale if **H.3368** (pending) conforms SC to
OBBBA mid-season.

**What would change our mind:** if H.3368 is enacted, the §179 figures jump to $2.5M/$4M and bonus
treatment changes — all depreciation/§179 logic is stale until re-verified (W2). If an SCDOR source
later pins a different 2025 §179 figure, switch Reading A → the stated figure. If the ATB
active/passive segregation (I-435 Col C, W4) needs to be computed rather than direct-entered, that
is a later reconcile-leg call. SC1120S multi-state Schedule G/E/H apportionment + the license-fee
apportionment were RED-deferred for v1 and can be built if demand warrants.

---

## 2026-07-05 — D-8: GA-700 v1 scope is MAXIMAL — full PTET compute (5.19% entity-level), §179 delta computed, Schedule 4 + 4% NRW computed

**Decision:** The GA Form 700 (Georgia partnership return, TY2025) v1 spec — the **1st partnership-entity
state return** in RS (GA600S S-corp + GA Form 500 individual precede it) — is scoped MAXIMAL per Ken's
2026-07-05 walk (4 AskUserQuestion decisions, all recommended): (A) **COMPUTE the full PTET path** (HB
149 / §48-7-21) — the elective entity-level tax = GA taxable income × **5.19%** (Sch 1 L7), gated on the
Form 700 page-1 election checkbox, plus the owner-side **PTEDED (Form 500 Sch 1 L12 subtraction) /
PTEADD (L5 addition)** mechanics and the credits-and-NOLs-stay-with-the-entity rules; (B) **COMPUTE the
§179 GA-limit difference** (GA **$1,050,000/$2,620,000**, not the federal OBBBA $2.5M/$4M) + model the Sch
5 L7 (federal-depr add-back) / Sch 6 L4 (GA-depr subtraction) structure, and **direct-entry** the
asset-level GA Form 4562 depreciation figures (the MACRS recompute the engine can't yet reach); (C)
**COMPUTE Schedule 4 partner allocation** (resident reports full share / nonresident reports GA-apportioned
+ allocated, with guaranteed-payment handling — the IT-711 p.13 worked example is the test oracle) + the
**4% nonresident withholding** (§48-7-129, <$1,000-share exemption, displaced when PTET is elected); (D)
**direct-entry** Schedule 10 credits + intangible/REIT add-backs, **RED-defer** GA NOL (Sch 9, 80% limit),
composite return (IT-CR), the UET underpayment penalty (Form 600UET, incl. its 5.75% prior-year quirk),
and credit pass-through allocation (Sch 11). Structure/constants verified against the FINAL 2025 GA DOR
sources (Form 700 Rev. 09/11/25; IT-711 booklet; HB 149 FAQ; Reg. 560-7-3-.03) — see [ga700_source_brief.md].

**Context:** August RS state track ("GA-700 + PTET"). GA Form 700 starts from FEDERAL partnership income
(Sch 8 ≈ federal Sch K), applies GA additions/subtractions (Sch 5/6), apportions by a **single
gross-receipts factor** (Sch 7, 6 decimals — the GA600S loader's "3-factor" note was STALE), and taxes at
the flat 5.19% only when the PTET election is made. PTET is the headline reason to build GA-700 now (the
federal SALT-cap workaround). Ken is a depreciation CPA, hence (B) computes the §179 delta.

**Divergence from precedent (called out):** the GA600S loader (`load_remaining_1120s.py`) records the PTET
rate as **5.49%** and apportionment as "property/payroll/sales" 3-factor — BOTH stale. GA-700 pins the
DOR-primary **5.19%** (2025) and the single gross-receipts factor. GA's PTET base is a **single
entity-level number** (federal taxable income with C-corp limits → §48-7-27 GA adjustments → §48-7-31
apportionment), NOT a resident/nonresident split (correcting the initial framing).

**What would change our mind:** if the GA-4562 asset-level recompute is needed for a correct return the
spec can't reach, (B)'s depreciation-subtraction stays direct-entry (as scoped). If the 2025 GA conformity
bill (not yet posted — §10 flag 1) moved the §179 figures or the conformity date, those constants are
stale until re-verified. If GA600S later needs the same 5.19%/single-factor correction, treat this as the
precedent (its 5.49%/3-factor is a logged reconstructability-adjacent drift, not authority).

---

## 2026-07-04 — D-7: NC D-400 v1 scope is MAXIMAL — resident + Schedule PN, the 85% bonus/§179 add-back is COMPUTED, Schedule S subtractions modeled structured

**Decision:** The NC D-400 (North Carolina individual, TY2025) v1 spec — the 4th state individual spec
after GA Form 500, SC1040, AL Form 40 — is scoped MAXIMAL per Ken's 2026-07-04 walk (4 AskUserQuestion
decisions, all recommended): (A) compute the full-year **resident** D-400 AND **Schedule PN** (part-year/
nonresident taxable-percentage proration → D-400 line 13 → line 14 = line 12b × the PN decimal); (B)
**COMPUTE** the current-year depreciation add-back — 85% of federal bonus depreciation (Schedule S Part A
line 3) + 85% of the IRC §179 excess over NC's **$25,000/$200,000** limits (Part A line 4) — and
**direct-entry** the 20% prior-year (2020-2024) recovery installments (Part B lines 23a-e/24a-e), which
need historical records the spec cannot reach; (C) **model L18 (US-obligation interest) / L19 (SS/RR) /
L20 (Bailey Settlement) / L21 (military retirement) as structured** Schedule S Part B line items with
eligibility diagnostics, not a single collapsed total; (D) **direct-entry** D-400TC credits (L16) +
consumer use tax (L18) + contributions (L30-32), and **RED-defer** Schedule PN-1, amended-return lines
(L22/L24, Schedule AM), the L26e estimated-tax underpayment interest (Form D-422), and the NC NOL (L39).
Structure/constants verified against the FINAL 2025 NCDOR PDFs (Form D-400 & Schedule S rev "Web-Fill
9-25"; D-401 booklet 2025) — see [nc_d400_source_brief.md]; **flat rate 4.25% (0.0425)**, standard
deduction $12,750/$25,500/$19,125, child-deduction AGI-banded table ($3,000→$0), conformity frozen at
**Jan 1, 2023 (OBBBA not adopted)**.

**Context:** August RS state track ("NC D-400 next" after SC1040 + AL Form 40). NC starts from FEDERAL
AGI (like GA-500; contrast SC's federal-taxable-income start and AL's from-scratch build) and is a FLAT
rate — the return's complexity is in the Schedule S conformity add-backs and the child-deduction table.
Ken is a depreciation CPA, hence (B) computes the add-back rather than deferring it — consistent with
SC1040 D-6's choice to compute the §168(k) add-back and diverging from GA-500 W1's direct-entry.

**Divergence from precedent (called out):** GA-500 v1 took depreciation decoupling as preparer
direct-entry (GA-500 W1). NC D-400 (B), like SC1040 (B), **computes** the current-year add-back. Unlike
SC (a single §168(k) bonus add-back), NC needs BOTH the 85% bonus add-back AND the 85% §179-excess
add-back (federal §179 − NC §179 at $25k/$200k), plus recognition that the 20% recovery installments are
a separate, historical-record-dependent direct-entry surface.

**What would change our mind:** if the add-back compute turns out to need asset-level data the spec
can't reach cleanly (the §179-excess needs both the federal and NC §179 figures), (B) may fall back to
direct-entry for v1 with the compute deferred to the depreciation-engine integration — a Ken call at the
reconcile leg. If NC issues a mid-season conformity update (the booklet warns to check), the 85%/limits/
rate constants are stale until re-verified.

---

## 2026-07-04 — D-6: SC1040 v1 scope is MAXIMAL — full resident + Schedule NR, and the §168(k) depreciation add-back is COMPUTED

**Decision:** The SC1040 (South Carolina individual, TY2025) v1 spec — the 2nd state individual
spec after GA Form 500 — is scoped MAXIMAL per Ken's 2026-07-04 walk (4 AskUserQuestion decisions):
(A) compute the full-year **resident** form AND **Schedule NR** (part-year/nonresident 3-column
SC-source proration → Sch NR line 48 → SC1040 line 5); (B) **COMPUTE** the line-e IRC §168(k)
bonus-depreciation add-back (SC non-conformity), NOT preparer direct-entry; (C) compute the full
**retirement / military / age-65 deduction stack** (the interacting reductions — SC's center of
gravity); (D) **RED-defer** the niche items (I-335 active-trade 3% election L8/line-l, SC4972
lump-sum L7, catastrophe-savings L9) each as a "prepare manually" diagnostic, and **direct-entry**
SC1040TC other credits (L13). Structure/constants verified against the final 2025 SC DOR PDFs
(SC1040 Rev. 4/21/25; SC1040TT Rev. 6/17/25) — see [sc1040_source_brief.md]; top rate 6% (down from
6.4%), 3 brackets 0/3/6% at $3,560/$17,830, $642 rate-schedule constant.

**Context:** August RS state track ("SC1040 — CC drafts, Ken walks — GA-500 pattern"). SC starts from
FEDERAL TAXABLE INCOME (contrast GA-500's federal AGI start). Ken is a depreciation CPA, hence the
choice to COMPUTE the §168(k) add-back rather than defer it.

**Divergence from precedent (called out):** GA-500 v1 took its depreciation/conformity decoupling as
**preparer direct-entry** (GA-500 W1). SC1040 (B) instead **computes** the §168(k) add-back. This
requires pinning SC's TY2025 IRC conformity date + the bonus add-back formula (federal depr − depr-
without-bonus), §179 conformity, and the future-year subtraction/basis-difference mechanics — a
follow-up research pass was dispatched 2026-07-04 to verify these against SC sources before authoring.

**What would change our mind:** if SC's conformity/bonus mechanics turn out to need asset-level data
the spec can't yet reach cleanly, (B) may fall back to direct-entry for v1 (matching GA-500) with the
compute deferred to the depreciation-engine integration — a Ken call at the reconcile leg.

---

## 2026-07-04 — D-5: Spec approval (draft→approved) is source-controlled via a manifest, not a DB edit

**Decision:** A spec's approval state is recorded in **source control** — `specs/approved_specs.py`
(`APPROVED_FORMS`, one entry per Ken-signed-off form) — and applied to the DB by the
`approve_specs` management command, which `seed_all` runs as its final phase (5). Approval is
NEVER set by a one-off DB edit. A from-scratch rebuild (`seed_all`) therefore restores every
approval from the manifest. `approve_specs` also reports drift: manifest entries with no matching
form, and forms approved in the DB but absent from the manifest (which would be lost on rebuild).

**Context:** The `TaxForm.status` field (draft/review/approved/archived) already existed, and every
loader seeds the model default `draft` (verified: all 88 forms were `draft`). The July checklist
item "begin the draft→approved workflow" needs a way to mark Ken-approved specs. The 2026-07-04
reconstructability check ([reconstructability_check.md]) had just proved that any state living only
in Supabase (not reproducible from loaders) silently drifts and is lost on rebuild.

**Alternatives considered:**
- Flip `status` directly in the DB / via Django admin — rejected: approval would vanish on the next
  `seed_all` (loaders re-seed `draft`); it is exactly the "lives only in Supabase" anti-pattern the
  reconstructability check cleaned up.
- Have each loader set its own `status=approved` — rejected: scatters approval across ~60 loaders,
  couples a sign-off to a code edit of the spec loader, and gives no single audit of "what Ken
  approved." A central manifest is one diffable list.

**What would change our mind:** if approval needs per-version or per-jurisdiction granularity beyond
what `form_number` (+ optional `jurisdiction`) gives, extend the manifest entry schema. If the app
grows a UI-driven review workflow, the manifest becomes the export target of that UI rather than a
hand-edited file.

---

## 2026-07-04 — D-4: S3/S4 unblock campaign — Schedule A (8936) is a separate spec (key 8936_SCHA); OBBBA gates are first-class year-keyed gates

**Decision:** Authoring the four MeF-ATS-blocking specs (4835, 8835, 8936, Schedule A
(8936)), three sub-decisions: (a) **Schedule A (Form 8936) is exposed as its OWN RS form
under the canonical lookup key `8936_SCHA`** (not folded into the 8936 export), following
the `1120S_SCHL` convention — it is a distinct IRS form (Cat. 93602W, Attach. Seq. 69A),
per-vehicle, while 8936 aggregates. (b) **The OBBBA termination gates are encoded as
first-class, year-keyed, highest-precedence gates**, not buried in prose: 8936's
"acquired after 9/30/2025 → no credit" runs per-vehicle on Schedule A before any credit
math (`R-8936SA-OBBBA` / `D_8936_001`), and 8835's "construction begins before 2025"
runs per-facility (`R-8835-OBBBA` / `D_8835_001`); both cutoffs live in year-keyed dicts
(`OBBBA_ACQUIRED_CUTOFF`, `SEC45_BEGIN_CONSTRUCTION_CUTOFF`) so TY2026 forces a re-verify
rather than silently reusing 2025. (c) **Disputed dollar amounts are left UNPINNED and
flagged, not guessed** — the S4 new-vehicle tentative credit is blank on the scenario
form (it comes from the seller report), so the S4 test asserts the gates + routing and
carries the credit amount as `[VERIFY-ATS-KEY]`; the $3,750/$7,500 §30D(b) tiers are
cited to the statute, not to Form 8936 (which doesn't print them).

**Context:** Ken's campaign prompt directed authoring all four so the tts app can build
S3 (Form 4835) and S4 (8936 + Schedule A + 8835). The prompt supplied tts-authored notes
transcribed from the 2025 DRAFT forms; the Authoritative-Source Rule required re-verifying
against the FINAL 2025 forms + instructions before locking (done via two subagents that
read the final PDFs verbatim). The OBBBA (P.L. 119-21) energy-credit terminations are the
highest-risk items and TY-sensitive.

**Alternatives considered:**
- Fold Schedule A into the 8936 export (one lookup key) — rejected: the tts build computes
  per-vehicle Schedule A then aggregates; a separate spec mirrors that and matches the
  probed `8936_SCHA` key + the `1120S_SCHL` precedent.
- Encode the OBBBA cutoffs as inline constants for 2025 only — rejected: violates the
  year-keyed-constants rule; a 2026 return would silently reuse the 2025 gate (and TY2026
  the credits are gone entirely).
- Assume $7,500 for the S4 EV credit to make the test concrete — rejected: the notes and
  the form both say the tentative credit is seller-reported; guessing it would encode a
  likely-wrong number (the BMW i4 is import-assembled and may not qualify at all).

**Reasoning:** Separate-form modeling keeps the per-vehicle → aggregate flow honest and
reusable. First-class year-keyed gates make the season-critical OBBBA terminations
auditable and re-verify-forcing. Leaving disputed dollars unpinned honors the
"flag, don't guess" tax-law rule and pushes the resolution to the ATS answer key / engine
where it belongs.

**Would reconsider if:** the tts build finds the aggregation cleaner with Schedule A
folded into 8936; or the ATS answer key pins the S4 tentative credit (then update the S4
test from `[VERIFY-ATS-KEY]` to the confirmed amount).

---

## 2026-07-04 — D-3: Form 4835 loss path FULLY COMPUTED (not RED-deferred); SE-exclusion is a hard invariant

**Decision:** The Form 4835 (Farm Rental Income and Expenses) spec computes the full
net-loss path — §465 at-risk (Form 6198) THEN §469 passive (Form 8582, incl. the
$25,000 active-participation special allowance) — rather than RED-deferring a loss
the way Schedule F does. It integrates with the EXISTING RS `FORM_8582` (Sch E loader)
and `6198` (1120-S loader) specs; it does not re-author them. Two companion rulings in
the same unit: (a) a HARD SE-EXCLUSION INVARIANT — no 4835 amount (line 32 income,
line 34c loss) may ever enter the Schedule SE base (line 1a/2 or the farm-optional
gross farm income); `R-4835-SE-EXCLUSION` + `FA-1040-4835-05` + `D_4835_SE_GUARD`
enforce it (§1402(a)(1)); and (b) a material-participation FORM-SELECTION guard —
`D_4835_MATPART` routes a materially-participating filer to Schedule F.

**Context:** Ken directed the loss path be computed because Form 4835 is in the MeF
(Modernized e-File) test set: an e-filed 4835 with a deductible loss must carry the
correct line-34c value and the 8582/6198 linkage in the XML, so a RED-defer (which
Schedule F uses for its own passive/at-risk loss) would leave the MeF case untestable.
The discovery that both limiter forms already exist in RS made computing — not
deferring — the cheaper correct option.

**Alternatives considered:**
- RED-defer the 4835 loss (the Schedule F precedent) — rejected: leaves the MeF
  loss case uncomputable; and unlike Sch F (where 8582/6198 weren't yet wired) the
  limiter specs are already available to integrate.
- Re-author 8582/6198 inside the 4835 unit — rejected: duplicates existing specs and
  would fork the passive/at-risk machinery. The 4835 activity registers as an input
  activity into the shared computations instead (flow assertions are the contract).

**Reasoning:** Computing through the existing limiters gives MeF-grade correctness at
integration cost, not re-implementation cost. The SE-exclusion invariant is the form's
defining trait (its subtitle is literally "Income Not Subject to Self-Employment Tax")
and is exactly the wiring bug a copy-paste from the Schedule F SE feed would introduce
— so it is asserted, not just documented.

**Would reconsider if:** the FORM_8582 per-activity allocation (Parts IV-VIII) turns
out not to accept a farm-rental activity in the active-rental-RE bucket (walk item B),
or a future MeF schema change alters the 4835→Sch E line-40 / 8582 linkage.

---

## 2026-07-04 — D-2: 1041 Schedule I (AMT) RED-DEFERRED for season one

**Decision:** Do NOT author or build the Form 1041 Schedule I (Alternative Minimum
Tax — Estates and Trusts) compute for season one. Instead, wire a loud RED
diagnostic that fires when a trust return shows AMT indicators, telling the
preparer the AMT path is out of scope and must be handled manually. Build the
real Schedule I spec + compute later only if demand warrants. This is one of the
two "Ken rulings" recorded on the RULE STUDIO AUTHORING TRACK in
`tts-tax-app/SEASON_CHECKLIST.md`; the companion is D-1 (1065 core specs are
authored fresh from IRS primary sources, then the existing 35 compute formulas
are reconciled against each spec — never spec-from-code; every mismatch is a
logged Ken adjudication).

**Context:** The September 1041 authoring wave (spine → DNI/IDD/Sch B → Sch G /
K-1 / GA 501) has to fit the season-one runway. Schedule I is a large, low-frequency
surface for this firm's trust population, and building it correctly would consume
walk-and-reconcile time better spent on the DNI/IDD core that every fiduciary
return touches.

**Alternatives considered:**
- Build Schedule I fully in season one — rejected: cost far exceeds the frequency
  it would actually be exercised at, and it crowds out the DNI/IDD spine.
- Silently omit it (no diagnostic) — rejected: violates the never-silent rule; a
  trust with AMT indicators would produce a wrong return with no warning.

**Reasoning:** A RED-deferred diagnostic gives the correctness guarantee (no
silently-wrong AMT return) without the build cost, and defers the real work to a
point where observed demand can justify it. Mirrors the established RED-defer
pattern used elsewhere in the suite (e.g. RRTA on 8959).

**Would reconsider if:** Trust returns with AMT exposure show up often enough in
the TaxWise regression bed to justify the build, or a state/federal change forces
Schedule I into a common path.

---

## 2026-04-27 — <Short decision title>

**Decision:** <what we chose>

**Context:** <the problem or question that forced a choice>

**Alternatives considered:** <what else was on the table and why we passed>

**Reasoning:** <why this option won>

**Would reconsider if:** <what new information would flip this>

---

## 2026-04-27 — <Short decision title>

**Decision:**

**Context:**

**Alternatives considered:**

**Reasoning:**

**Would reconsider if:**

---

<!-- Append new entries at the top. Older decisions remain below. -->
