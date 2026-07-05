# 1065 Core — D-1 Reconcile Log (spine leg)

*Per D-1 + brief §2: each fresh RS spec is diffed against the existing tts compute formulas;
every mismatch is a logged Ken adjudication. This log covers the SPINE leg (`1065_PAGE1` +
`SCH_K_1065`), authored 2026-07-04, `READY_TO_SEED=False`. Fill/resolve at the Ken walk BEFORE
flipping to seed. tts reconcile targets (read-only survey 2026-07-04):
`server/apps/returns/compute.py` (entity Schedule K block, ~lines 240-298), `compute_schedule_k1.py`
(recipient/1040 side), `k1_allocator.py` (allocation — the K-1 leg's target).*

| # | RS spine formula | tts compute | Status | Ken call |
|---|---|---|---|---|
| 1 | Page-1 **total deductions = line 22** (Σ 9-21); **ordinary business income = line 23** (8 − 22); Sch K line 1 ← **line 23** | `compute.py:265-268`: field `"21"` = Σ(9-20) = total deductions; field `"22"` = 8 − 21 = ordinary income; `:282` `K1 ← "22"` | ⚠ **LABEL MISMATCH (off-by-one)** — arithmetic identical, tts internal field keys trail the FINAL 2025 face by one | Keep tts internal keys + map `"22"`→face line 23 at build, OR renumber tts page-1 to the 2025 face. Also confirm tts Σ(9-20) captures "other deductions" (face line 21) — verify no dropped line. |
| 2 | Page-1 **line 8 total income = Σ(3-7)** (`R-1065P1-8`) | `compute.py:240`: `("8", Σ "3","4","5","6","7")` | ✅ **MATCH** | none |
| 3 | Sch K **3c = 3a − 3b** (`R-SCHK-3C`) | `compute.py:284`: `("K3c", K3a − K3b)` | ✅ **MATCH** | none |
| 4 | Sch K **14a** = the `1065_SE` spec (bottom-up Σ per-partner box 14a; `R-SCHK-14A`) | `compute.py:288-292`: K14a derived bottom-up by `compute_1065_se_db` (RECON-14A) | ✅ **MATCH** (already reconciled this season) | none |
| 5 | Sch K **§179 → line 12** (`k_12_section_179`) | `compute.py:984`: `sec179_line = "K12" if form_code=="1065"` | ✅ **MATCH** | none |
| 6 | **Analysis of Net Income line 1 = (Σ K 1-11) − (Σ 12-13e + 21)** (`R-SCHK-ANALYSIS`) | tts has **no** 1065 Analysis computation — `K18` (`compute.py:120`) is the **1120-S** income reconciliation only | 🔨 **GAP — build item** | Implement the 1065 Analysis line 1 in tts (ties to M-1 line 9 / M-2 line 3 for the L/M leg). New. |
| 7 | Net farm profit on **page-1 line 5** → total income → ordinary income → K1 (`p1_5_net_farm`; face f1065 line 5) | ~~`compute.py:287`: `("K11", F34)`~~ **FIXED** — now `("5", F34)` → line 8 → K1 | ✅ **FIXED in tts (`f61cfec`, 2026-07-04)** — Ken: "fix now" | **Was a CONFIRMED bug** (misroute + latent double-count): `seed_1065.py` seeds BOTH a page-1 line 5 (`:80`) AND a full enterable Schedule F block F1a-F34 (`:223-262`); `FORMULAS_1065` computed `F34=F9−F33` INLINE (`:278`) and routed to **K11** (`:287`). Failure modes: (a) Schedule F block only → farm on **K11 not K1** → 14a SE base (reads K1 only, `compute_1065_se`) **omits farm → SE understatement**; (b) F-block + hand-entered line 5 → **DOUBLE-COUNT**. **Fix:** relocated the Schedule F block ahead of page-1 line 8, added `("5", F34)` so farm flows line 5 → 8 → 22 → **K1** (and the SE base); removed `K11←F34`; `seed_1065` line 5 `is_computed=True` (YELLOW). Regression: `TestNetFarmRouting` (3/3 green, shared test DB). |
| 8 | Sch K **9c unrecaptured §1250** ← 4797 aggregate; allocates to K-1 box 9c (`R-SCHK-9C` / `D_SCHK_9C`) | `aggregate_dispositions` → K9c (tts fix `f23dc54`); `k1_allocator` K9c→box 9c (LT_CAPITAL) | ⚠ **OPEN** — downstream box-9c partner pass-through not separately re-verified | Ties to the STILL-OPEN tts verification (STATUS Next-up). Confirm at the K-1 leg. |

## Notes carried to the K-1 + allocation leg (next form)

- **§704(b)/(c) allocation MATH** (Decision C: structure encoded here, math deferred): the K-1 leg
  reconciles `k1_allocator.py` — how much §704(b) substantial-economic-effect / §704(c)
  reasonable-method it already models vs. RED-defer. `k_has_704c_property` / `k_has_special_alloc`
  gating flags + `D_SCHK_704C` surface the item M/N case now.
- **K → K-1 box map** (`R-SCHK-KMAP`): reconcile the 1:1 (boxes 1-10) vs coded-collapse
  (11/13/14/15/17-20) mapping against `compute_schedule_k1.py` consumers (`k1_interest_total`,
  `k1_st/lt_capgain_total`, `k1_section_1231_total`, `k1_qbi_total`, …) at the K-1 leg.
- **Box 16 → K-3 checkbox** (Decision A RED-defer): `D_SCHK_K3` / `GATE-K2K3-DEFER` mark the
  international scope boundary.

---

# 1065 Core — L/B Leg Reconcile (form 4: Schedule L + Schedule B)

*Authored 2026-07-04, `READY_TO_SEED=False`. `load_1065_l_b.py` seeds `1065_L` + `1065_B`, fresh
from the FINAL 2025 f1065 (page 6 Schedule L; pages 2-4 Schedule B, 33 Qs, pymupdf verbatim) +
primary IRC (§705/§754/§448(c)/§6221, Cornell LII verbatim). tts reconcile targets (read-only
survey 2026-07-04 via Explore agent): `compute.py` Schedule L totals (~L313-329) +
`compute_schedule_l()` (~L1619-1715) + `seed_1065.py` (L/B field seed).*

| # | RS L/B formula | tts compute | Status | Ken call |
|---|---|---|---|---|
| L1 | Sch L **line 14 total assets = Σ asset lines** (2a−2b, 9a−9b, 10a−10b, 12a−12b netted); **line 22 = Σ 15-21** (`R-L-14` / `R-L-22`) | `compute.py:313-329`: `L15` = Σ net asset lines; `L24` = Σ(L16..L23). BOY(a)+EOY(d) | ✅ **MATCH** (arithmetic identical) | none |
| L2 | Sch L **numbering = the 2025 face 1-22** | tts uses **L1-L24** — splits face 7a/7b→L7/L8 and 19a/19b→L20/L21, shifting the tail one (tts L15=face14, L23=face21, L24=face22) | ⚠ **LABEL MISMATCH (off-by-one, same shape as page-1)** | **Decision D:** author RS to the FACE (1-22); map tts L1-L24→face at build, OR renumber tts. RECOMMEND face. |
| L3 | **R-L-BALANCE** — line 14 == line 22 (both cols) + `D_L_BALANCE_{BOY,EOY}` | tts computes L15 + L24 but **NEVER compares** them; no out-of-balance diagnostic | 🔨 **GAP — build item** | Add the balance check to tts (new studio validation `RECON-L-BALANCE`). |
| L4 | **R-L-21-TIE** — line 21 partners' capital EOY = M-2 line 9; BOY = M-2 line 1 (tax basis) | tts `L23d` (=face 21) is **data-entry**; `M2_9` computed; **no reconciliation** between them | 🔨 **GAP — build item** | Reconcile L21↔M-2 in tts (carries the M-2 leg tie home; `D_L_21_M2_TIE`). |
| L5 | Sch L **9b/12b EOY accum. depreciation/amortization** = data-entry or computed-pull (YELLOW) | `compute_schedule_l()`: **L10d/L10e + L13d/L13e AUTO-COMPUTED** from `DepreciationAsset` (BOY + additions − dispositions; accum + current-yr − disposed) | ✅ **MATCH-plus** (tts AHEAD) | none — RS models 9b/12b EOY as computed-pull (YELLOW), consistent with tts's roll-forward. |
| B1 | Sch B **Q4 = 4a AND 4b AND 4c AND 4d** → the `m_schb_q4_small` gate suppressing L/M-1/M-2/item F/K-1 item L (`R-B4-SMALL`) | tts seeds `B6` (=face Q4) as a **data-entry boolean**; **NO gating logic** auto-suppresses L/M | 🔨 **GAP — build item** | Make Q4 a computed gate in tts + wire the suppression (`GATE-SMALL-PTNR-B`). THE load-bearing gap. |
| B2 | Sch B **Q24 = 24a OR 24b OR 24c** ($31M §448(c)) → Form 8990 (`R-B24-8990`) | tts seeds `B16` (=face Q24) data-entry; **no $31M threshold logic** | 🔨 **GAP — build item** | Compute the §163(j)/§448(c) $31M trigger in tts (`GATE-8990-163J`). |
| B3 | Sch B **33 questions** (2025 face, verbatim) | tts seeds **18 condensed questions** (`B1-B18`); B6=Q4, B16=Q24 | ⚠ **COVERAGE MISMATCH** | Face-only Qs absent from tts's 18: Q22 §267A, Q25 QOF (8996), Q26 §864(c)(8), Q27 Reg 1.707-8, Q29 Form 7208. Expand tts to 33 or keep the condensed map. RS authored to the full face (authority). |
| B4 | **Q10 §754/§743(b)/§734(b)** — election + amounts captured + flagged; basis-adjust **MATH RED-deferred** (`R-B10-754`, `D_B10_754`) | tts `B12a`/`B12b` data-entry booleans; no basis-adjust compute | ⚠ **Decision E RED-defer** | Confirm §743(b)/§734(b) basis-adjustment math is out of season-one scope (structure/flag only). |
| B5 | **M-3 threshold** L14 ≥ $10M / receipts ≥ $35M → M-3 replaces M-1 (`R-L-M3`, `D_L_M3`, flag only) | tts has no M-3 threshold logic | ⚠ **Decision F RED-defer** | Confirm Schedule M-3 (+ B-1/B-2/B-3 sub-schedules) stay RED-deferred; flag + attachment-triggers only. |

## Scope decisions proposed for the Ken walk (carry the spine A/B/C posture)

- **D — Schedule L numbering:** author RS to the 2025 FACE (1-22); log tts's L1-L24 offset (L2) as a
  build remap. RECOMMEND face (RS is the authority spec).
- **E — §754/§743(b)/§734(b) basis-adjustment MATH (Q10):** RED-defer — structure + cited authority
  (§754 verbatim) + flag only; the basis-adjustment computation is a future leg (brief §4.1 concurs).
- **F — Schedule M-3 + B-1/B-2/B-3 sub-schedules:** RED-defer (carries Decision B). M-3 threshold
  surfaces as an INFO/warning diagnostic (`R-L-M3`); B-1/B-2/PR modeled as attachment-trigger flags.
- **G — Schedule L depth:** FULL a/b sub-lines (2a/2b, 9a/9b, 10a/10b, 12a/12b) — matches the
  1120S_SCHL precedent + tts + Ken's depreciation focus (accum. depreciation on 9b is load-bearing).

**On the Ken walk + "flip seed export": set `READY_TO_SEED=True` → seed → export → verify
`lookup/{1065_L,1065_B}/export/` 200.**

---

# 1065 Core — CAMPAIGN CLOSE (forms 5 & 6 coverage confirmation)

*2026-07-04. Forms 5 & 6 = 8825 / 4562 / 3800. Per the brief §1 these already exist as multi-entity;
this leg CONFIRMED that against the LIVE RS DB (not just the brief table) — both the entity tag AND the
actual 1065 routing wiring.*

| Form | `entity_types` (live DB) | 1065 routing wired? | Verdict |
|---|---|---|---|
| 3800 | `['1120S','1065','1120','1040']` | GBC entity-agnostic aggregation (12 rules) | ✅ covers 1065, no fresh authoring |
| 4562 | `['1120S','1065','1120','1040']` | **R004** "§179 flows to Schedule K (not Page 1)" + R014 line-12 §179 | ✅ covers 1065, no fresh authoring |
| 8825 | `['1120S','1065']` | **R003** "Total net rental → K Line 2" (exact 1065 Sch K line 2 handoff) | ✅ covers 1065, no fresh authoring |

**Campaign COMPLETE (6/6):** spine (`1065_PAGE1`+`SCH_K_1065`), K-1+alloc (`SCHEDULE_K1_1065`), M-1/M-2
(`1065_M1`/`1065_M2`), L/B (`1065_L`/`1065_B`) fresh-authored + seeded + exported (all endpoints 200);
8825/4562/3800 pre-existing, confirmed 1065-wired. RS side CLOSED. Remaining items are all tts-side build
gaps (logged above + STATUS Next-up) — none are RS blockers.
