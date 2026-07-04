# 1065 Core — Source Brief (pre-staged for the July campaign)

*Prepared 2026-07-04 during the S3/S4 unblock session, as forward prep for the **1065 core**
authoring campaign (season checklist, July). This is a TRANSCRIPTION AID / reconcile map —
**NOT a spec and NOT authorization to seed.** Per **D-1**, the 1065 core is authored FRESH
from IRS primary sources, then reconciled against the existing tts compute formulas, and every
mismatch is a logged Ken adjudication. Verify each line against the FINAL 2025 source before
locking; the verbatim line maps below were fetched from the final 2025 PDFs (see §4).*

---

## 1. Why this campaign / what's the gap

The 1040 MeF ATS track is done (S3/S4 unblocked this session). The next RS campaign is the
partnership core. Cross-referencing the season plan against the 82 seeded RS specs, the 1065
entity-side forms are almost entirely unbuilt — the 1120-S family exists, but its 1065
counterparts do not.

| 1065-core form | RS today | Action |
|---|---|---|
| Form 1065 page 1 (ordinary business income) | `1065` is an **empty stub** (entity=`[]`, mislabeled "1065_SE") | **author fresh** |
| Schedule K (partners' distributive share spine) | only `SCH_K_1120S` (1120-S) | **author fresh** |
| Schedule K-1 (Form 1065) + allocation engine | only `SCHEDULE_K1` (entity=`1040`, the recipient side) | **author fresh** |
| Schedule M-1 / M-2 | only `1120S_M1` / `1120S_M2` | **author fresh** |
| Schedule L | only `1120S_SCHL` | **author fresh** |
| Schedule B (1065 questions) | only `SCH_B` (entity=`1040`, interest/dividends) | **author fresh** |
| Form 8825 (1065) | `8825` entity=`['1120S','1065']` | ✅ **exists** |
| Form 4562 / Form 3800 | multi-entity (incl. 1065) | ✅ exists |
| 1065 Sch K line 14a (SE) | `1065_SE` (entity=`1065`) | ✅ **exists** (this season) |

Suggested authoring order (spine first, the season-checklist order): **Schedule K →
Schedule K-1 + allocation engine → M-1 / M-2 → L / B → (8825 already done).** Page 1 ordinary
income feeds Schedule K line 1, so page 1 pairs with the Schedule K unit.

---

## 2. Reconcile targets in tts (the D-1 "35 compute formulas" side)

The fresh specs reconcile against these existing tts compute modules (read-only survey, this
session — do NOT edit; the parallel session is elsewhere):

- **`server/apps/returns/k1_allocator.py`** — the allocation engine. Key fns: `allocate_k1()`,
  `allocate_all_k1s()`, `resolve_se_classification()`. This is what the new Schedule K-1 +
  allocation spec must reconcile against (profit/loss/capital %, SE classification, special
  allocations). Already touched this season by the K9c fix + the 1065_SE unit.
- **`server/apps/returns/compute_schedule_k1.py`** — the recipient (1040) side K-1 aggregation
  (`schedule_k1_rows`, `k1_sche_net`, `k1_interest_total`, `k1_ordinary_dividends_total`,
  `k1_qualified_dividends_total`, `k1_royalties_total`, `k1_st/lt_capgain_total`,
  `k1_section_1231_total`, `k1_qbi_total`, `k1_reit_ptp_total`, `k1_199a_present`,
  `k1_se_by_owner`). Reconcile the K→K-1 box mapping (§4.2) against these consumers.
- **`server/apps/returns/compute_1065_se.py`** — `compute_1065_se_db()`, the Sch K line 14a
  SE-earnings computation (already specced as `1065_SE`; the reconcile is done for 14a).
- **`server/apps/returns/compute.py`** — the main return compute (entity-side Schedule K
  aggregation / page-1 ordinary income, if present). Survey for the 1065 page-1 → Sch K line 1
  path when authoring the Schedule K unit.

**Reconcile checklist (fill during the campaign):** for each new spec, diff its computed line
formulas against the tts fn above; log every mismatch as a Ken adjudication (D-1).

---

## 3. Known law/structure notes to encode (verify at the spec leg)

- **Schedule L / M-1 / M-2 exemption:** a partnership that answers "Yes" to the Schedule B
  total-receipts-under-$250,000 AND total-assets-under-$1,000,000 test (plus timely K-1s, no
  Sch M-3) is NOT required to complete Schedules L, M-1, M-2, or item L of the K-1. Encode as a
  gating fact so the spec doesn't demand a balance sheet that isn't required. (Exact 4-condition
  text + thresholds → §4.1, agent-verified.)
- **Schedule M-3** replaces M-1 at $10M+ total assets (or $35M+ receipts / reportable-entity-
  partner) — the 1120-S precedent has `1120S_M3`; the 1065 M-3 is likely out of season-one
  scope (flag, don't silently omit).
- **Schedules K-2 / K-3** (international) split off from line 16 post-2021 — box 16 now largely
  points to K-3. Confirm whether season one models K-2/K-3 or RED-defers them (likely defer).
- **Tax-basis capital reporting** (K-1 item L) is mandatory — the M-2 / item L tie-out.
- **§704(b) / §704(c)** special & built-in-gain allocations — the allocation engine's hard part;
  confirm how much the tts `k1_allocator` already handles vs. RED-defer.
- **OBBBA (P.L. 119-21)** partnership touches (bonus depreciation 100%, §179, §163(j), §461(l))
  flow through Form 4562 (specced) + page-1 deductions — verify the 2025 What's New (§4.1).

---

## 4. VERBATIM LINE MAPS (from the FINAL 2025 IRS sources)

> Fetched + verified 2026-07-04 by reading the final 2025 PDFs directly (f1065.pdf Cat. 11390Z
> "Created 11/25/25"; f1065sk1.pdf Cat. 11394R "Created 2/26/25"; i1065.pdf Cat. 11392V "Jan 14,
> 2026"; i1065sk1.pdf). All three subsections are COMPLETE and verbatim. The only [UNVERIFIED] item
> flagged: bonus depreciation / §179 / §461(l) TY2025 specifics are not in the 1065 What's New —
> verify those against the Form 4562 instructions (they ride page-1 line 16a). The full Schedule
> K-1 coded-box code lists (boxes 11/13/14/15/17/18/19/20, ~200 codes) were captured verbatim and
> should be transcribed at the K-1 authoring leg — this brief summarizes the notable/OBBBA codes.

### 4.1 Form 1065 page 1 (income & deductions) + Schedule B (questions)

*Source: Form 1065 (2025), Cat. No. 11390Z, "Created 11/25/25"; Instructions Cat. No. 11392V,
dated Jan 14, 2026. FINAL. Verbatim off the fetched PDFs.*

**⚠ Corrections to the common framing** (the 2025 form differs from the "23–30" mental model):
page-1 **ordinary business income = line 23** (not 22); **total deductions = line 22**; the
tax/payment block is **lines 24–32**; direct-deposit fields **32b/32c/32d are NEW for 2025**
(Exec. Order 14247). Schedule B has **33 questions** (not ~29).

**Page 1 — Income:** 1a gross receipts/sales · 1b less returns/allowances · 1c balance (1a−1b) ·
**2 COGS (← Form 1125-A)** · 3 gross profit (1c−2) · 4 ordinary income from other partnerships/
estates/trusts (attach stmt) · **5 net farm profit (← Schedule F)** · **6 net gain (← Form 4797
Part II line 17)** · 7 other income (attach stmt) · **8 total income = Σ lines 3–7.**

**Page 1 — Deductions:** 9 salaries/wages (less emp. credits) · 10 guaranteed payments to
partners · 11 repairs · 12 bad debts · 13 rent · 14 taxes & licenses · 15 interest · **16a
depreciation (← Form 4562)** · 16b less depr. on 1125-A/elsewhere · 16c balance · 17 depletion
(no oil/gas) · 18 retirement plans · 19 employee benefit programs · **20 energy-efficient
commercial buildings (← Form 7205)** · 21 other deductions (attach stmt) · **22 total deductions
= Σ lines 9–21.**

**Ordinary business income:** **23 = line 8 − line 22 → Schedule K line 1** (the key entity→K
handoff).

**Tax & Payment:** 24 look-back interest (Form 8697) · 25 look-back interest income-forecast
(Form 8866) · 26 BBA AAR imputed underpayment · 27 other taxes · 28 total balance due (Σ 24–27) ·
**29 elective payment election amount (← Form 3800)** · 30 payment · 31 amount owed · 32a
overpayment · 32b/32c/32d direct-deposit routing/type/account (NEW 2025).

**Schedule B ("Other Information") — 33 questions.** The load-bearing ones for the spec:

- **Q4 — the L / M-1 / M-2 exemption (verbatim):** *"Does the partnership satisfy all four of the
  following conditions? (a) total receipts for the tax year were less than **$250,000**; (b) total
  assets at end of year were less than **$1 million**; (c) Schedules K-1 are filed with the return
  and furnished to partners on/before the due date (incl. extensions); (d) the partnership is not
  filing and is not required to file Schedule M-3. If 'Yes,' the partnership is not required to
  complete Schedules L, M-1, and M-2; item F on page 1; or item L on Schedule K-1."* → encode as a
  gating fact (`f1065_sch_b4_small` or similar) that suppresses the L/M/itemL requirement.
- **Q10 §754 election:** 10a §754 election (+ effective date) · 10b §743(b) optional basis adj
  (net positive/negative amounts) · 10c §734(b) · 10d substantial-built-in-loss/basis-reduction ·
  10e reserved. (The basis-adjustment complexity — likely RED-defer beyond the flag.)
- **Q23 §163(j) RPTB/farming election;** **Q24 Form 8990 test** — 24b threshold: aggregate average
  annual gross receipts (§448(c)) over the 3 prior years **> $31 million** + business interest
  expense → attach Form 8990. (§163(j) small-business exemption pivots on this $31M figure.)
- **Q1 entity type** (general/limited partnership, LLC, LLP, foreign, other); **Q2a/2b** 50%-owner
  (Schedule B-1); **Q5** PTP (§469(k)(2)); **Q30 digital asset** question; **Q32 §761 election out
  of subchapter K;** **Q33 §6221(b) centralized-audit election out** (Schedule B-2) + **Partnership
  Representative designation** block (PR name/address/phone + designated individual if PR is entity).
- **NOT on Schedule B:** no standalone §704(c) question, no technical-termination question
  (§708(b)(1)(B) repealed by TCJA).

**TY2025 What's New (OBBBA / P.L. 119-21) affecting 1065 — verbatim highlights:**
- **§174A domestic R&E** — expenditures paid/incurred in tax years beginning after 2024 are
  current-year deductible (or elect ≥60-mo amortization under §174A(c)); small-business
  retroactive relief per Rev. Proc. 2025-28. **NEW — affects page-1/other-deductions treatment.**
- **§181** — qualified sound-recording production costs added as an elective expense → **Sch K/K-1
  line 13e code X** (productions commencing after 7/4/2025, before 2026).
- **§1062** — gain on sale of qualified farmland to qualified farmers, 4-installment election →
  **Sch K/K-1 line 20c code ZZ** (Form 1062).
- **Line 19 distributions** — additional codes activated (19a/19b category reporting).
- **Line 20 code AR** (IRA-partner UBTI EIN after 2025), **code AZ** (preformation expenditures).
- **Schedule B Q19** updated to include payments received allocable to foreign partners.
- **[UNVERIFIED from this source]** bonus depreciation / §179 / §461(l) are NOT in the 1065 What's
  New — they ride **line 16a via Form 4562** (verify against the 2025 **Form 4562** instructions;
  §461(l) is a **partner-level** limit, not on the 1065 return).

### 4.2 Schedule K (distributive share) + Schedule K-1 + the K→K-1 mapping

*Source: Form 1065 (2025) page 5 (Cat. 11390Z); Schedule K-1 (Form 1065) 2025 (Cat. 11394R, form
ID 651123, Created 2/26/25); Partner's Instructions i1065sk1 (2025) + i1065 (2025). Verbatim via
direct PDF text extraction (the WebFetch summarizer was unreliable on these — bypassed).*

**Schedule K — Partners' Distributive Share Items (page 5), col "Total amount":**
Income(Loss) — 1 ordinary business income **(= page-1 line 23)** · 2 net rental real estate (attach
Form 8825) · 3a other gross rental / 3b expenses / 3c net · 4a guaranteed pmts services / 4b capital
/ 4c total · 5 interest · 6a ordinary dividends / 6b qualified / 6c dividend equivalents · 7
royalties · 8 net ST capital gain (Sch D 1065) · 9a net LT capital gain / 9b collectibles 28% / 9c
unrecaptured §1250 · 10 net §1231 gain (Form 4797) · 11 other income (coded).
Deductions — 12 §179 (Form 4562) · 13a cash contrib / 13b noncash / 13c investment interest / 13d
§59(e)(2) / 13e other (coded).
Self-Employment — 14a net SE earnings **(= the `1065_SE` spec)** / 14b gross farming-fishing / 14c
gross nonfarm.
Credits — 15a-15f (LIHC ×2, rehab, other rental RE, other rental, other credits).
International — **16a/16b = checkboxes pointing to Schedule K-2** (no numbered intl lines remain).
AMT — 17a-17f. Other — 18a-18c (tax-exempt/nondeductible) · 19a/19b distributions · 20a-20c
(investment income/expense/other) · 21 total foreign taxes.
**Analysis of Net Income (Loss) per Return line 1 = combine Sch K lines 1–11, minus (lines 12–13e +
21).** Line 2 = analysis by partner type (corporate / individual active / individual passive /
partnership / exempt org / nominee-other).

**Schedule K-1 (Form 1065):**
- **Part I** A-D (EIN, name/addr, filing center, PTP checkbox).
- **Part II** E-N. Load-bearing for the allocation engine: **item J** partner's profit/loss/capital
  % (Beginning/Ending; + "decrease due to sale/exchange" flag) · **item K1/K2/K3** share of
  liabilities (nonrecourse / qualified nonrecourse / recourse; lower-tier flag; guarantee flag) ·
  **item L** capital account analysis (beginning + contributed + current-year net income/loss +
  other incr/decr + withdrawals/distributions = ending, **TAX BASIS**) · **item M** contributed
  built-in-gain/loss property? (Y/N) · **item N** net unrecognized §704(c) gain/(loss) (Beg/End).
- **Part III** boxes 1-23 (1-11 income, 12-13 deductions, 14 SE, 15 credits, 16 K-3-attached
  checkbox, 17 AMT, 18 tax-exempt/nondeductible, 19 distributions, 20 other, 21 foreign taxes, **22
  multi-activity at-risk flag, 23 multi-activity passive flag** — K-1-only). Top checkboxes: Final /
  Amended K-1.

**K → K-1 correspondence (what the allocation engine encodes):** boxes 1-10 (and 4/6/9 sub-lines)
map **1:1**. Every Schedule K *detail grouping* (lines 11, 13a-e, 14a-c, 15a-f, 17a-f, 18a-c,
19a-b, 20a-c) **collapses into a single coded K-1 box** (11, 13, 14, 15, 17, 18, 19, 20) where the
letter code (A–ZZ) identifies the underlying item. Line 3c → box 3 (net). **The one real
difference: Sch K line 16 → Schedule K-2 (partnership intl detail); K-1 box 16 → Schedule K-3
checkbox (partner copy)** — all international line detail lives in K-2/K-3, not on K/K-1.

**Allocation mechanics (verbatim i1065 p.31/34):** allocate per the partnership agreement;
specially-allocated items go on the applicable partner's K-1 line and total on Sch K (NOT the
numbered page-1 lines). **§706(d)** varying-interest (proration vs. closing-of-books for
mid-year interest changes). **§704(c)** — contributed property with FMV ≠ basis uses a reasonable
method so the contributing partner bears the built-in gain/loss (Reg. 1.704-3; tracked in items
M/N). **§704(b)** fallback — if no allocation or it lacks substantial economic effect, allocate by
partner's interest (Reg. 1.704-1). **Item L tax-basis** — transactional approach (§§705/722/733/742);
the ending item-L capital "might not equal" the partner's outside basis (basis includes liabilities).
`k1_allocator.py` is the reconcile target (D-1); confirm how much §704(b)/(c) it already models vs. RED-defer.

**Coded boxes — the code lists (11, 13, 14, 15, 17, 18, 19, 20) are captured in the agent transcript;
transcribe fully at the K-1 authoring leg.** Notables to encode / cross-reference now:
- **Box 15 credits** carry the credits I specced this session: **AY new clean vehicle (8936), AZ
  commercial clean vehicle (8936 Part V), AB renewable electricity production (8835), W clean
  electricity production (§45Y)** — the K-1 is how a partnership passes these to partners → the
  partner's 3800/8936/8835. This ties the 1065 core back to the S3/S4 work.
- **Box 20** codes the §199A (Z), §704(c) (AA), §751 (AB), §163(j) EBIE/excess-taxable-income
  (N/AE/AF), §448(c) gross receipts (AG), **AJ excess business loss (§461(l), partner-level)**.
- **Box 13 code X** expanded under OBBBA (§181 sound-recording, per §4.1). **Box 11 code F / box 13
  code V** = §743(b) positive/negative adjustments (the §754 tie from Sch B Q10).

### 4.3 Schedule L (balance sheet) + Schedule M-1 + Schedule M-2

*Source: Form 1065 (2025) page 6 (Cat. 11390Z); Instructions (Cat. 11392V) pp. 18/34/62/63.
FINAL, verbatim. Note: L/M-1/M-2 are on **page 6** (page 5 = Schedule K + Analysis of Net Income).*

**Schedule L — Balance Sheets per Books** (columns: beginning (a)/(b), end (c)/(d)):
Assets — 1 cash · 2a trade notes/accts receivable · 2b less allowance for bad debts · 3
inventories · 4 U.S. gov obligations · 5 tax-exempt securities · 6 other current assets · 7a loans
to partners · 7b mortgage/real-estate loans · 8 other investments · 9a buildings/other depreciable
assets · 9b less accum. depreciation · 10a depletable assets · 10b less accum. depletion · 11 land
· 12a intangible (amortizable) assets · 12b less accum. amortization · 13 other assets · **14 total
assets.** Liabilities & capital — 15 accts payable · 16 mortgages/notes/bonds < 1 yr · 17 other
current liabilities · 18 all nonrecourse loans · 19a loans from partners · 19b mortgages/notes/
bonds ≥ 1 yr · 20 other liabilities · **21 partners' capital accounts** · **22 total liab. & capital.**

**Schedule M-1 — Reconciliation (book → return)** (header: "may be required to file Schedule M-3"):
1 net income (loss) per books · 2 income on Sch K lines 1,2,3c,5,6a,7,8,9a,10,11 not on books ·
3 guaranteed payments (other than health ins.) · 4 expenses on books not on Sch K lines 1–13e & 21
(4a depreciation, 4b travel/entertainment) · 5 add 1–4 · 6 income on books not on Sch K lines 1–11
(6a tax-exempt interest) · 7 deductions on Sch K lines 1–13e & 21 not on books (7a depreciation) ·
8 add 6 and 7 · **9 = line 5 − line 8 → Analysis of Net Income (Loss) per Return, line 1.**

**Schedule M-2 — Analysis of Partners' Capital Accounts** (TAX-BASIS, transactional approach,
§§705/722/733/742): 1 balance BOY · 2 capital contributed (2a cash, 2b property net of liabilities)
· **3 net income/loss = Analysis line 1 (= M-1 line 9)** · 4 other increases · 5 add 1–4 · 6
distributions (6a cash, 6b property) · 7 other decreases · 8 add 6 and 7 · **9 = line 5 − line 8 =
balance EOY.** Tie-outs: **M-2 line 1 = Σ K-1 item L beginning tax-basis capital**; if Sch L is
tax-basis and the aggregate capital differs from L, attach a reconciliation (§743(b) adjustments &
guaranteed payments excluded from tax-basis capital — adjust via line 4/7).

**Exemptions/thresholds (encode as gating facts):**
- **Schedule B Q4** (all four → skip L, M-1, M-2, item F, and K-1 item L): receipts **< $250,000**
  AND assets **< $1,000,000** AND timely-furnished K-1s AND not-M-3-required.
- **Schedule M-3 replaces M-1** if: total assets (Sch L line 14 col (d)) **≥ $10M**, OR adjusted
  total assets **≥ $10M**, OR total receipts **≥ $35M**, OR a reportable-entity-partner owns
  **≥ 50%**. M-3 filers also file Schedule C (Form 1065). *(Likely season-one RED-defer — flag.)*

---

## 5. When Ken kicks off the campaign

1. Read §4 (verified line maps) + §2 (reconcile targets).
2. Author the Schedule K spec first (the spine), fresh from §4.2; READY_TO_SEED=False.
3. Walk the decisions with Ken (K-2/K-3 defer? M-3 scope? §704(c) depth?) — D-1.
4. Reconcile against `k1_allocator` / `compute_schedule_k1`; log mismatches.
5. Seed → export → verify `lookup/{form}/export/` 200 → next form.
