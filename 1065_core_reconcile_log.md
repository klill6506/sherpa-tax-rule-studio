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
