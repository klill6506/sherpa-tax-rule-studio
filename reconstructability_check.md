# RS DB Reconstructability Check — 2026-07-04

## ✅ UPDATE — August 1120-S delta audit COMPLETE (2026-07-05): prod ↔ rebuild is now 0-delta

The residual drift below is **fully resolved**. A fresh `seed_all` rebuild now matches production
**exactly** — 92 form_numbers, 0 form-set difference, **0 rule-level diff** across every form. Root
causes + fixes:

- **§A (SCH_K_1120S / SCHD_1120S "orphans") — ORDERING BUG, not orphans.** `load_1120s_full` *amends*
  those forms (adds R010-R018 / R010-R012) but wasn't in `seed_all`'s `AMEND_LOADERS`, so it ran
  alphabetically in phase 2 **before** its base `load_1120s_specs`; its `.first()` lookup returned None
  and the flow-detail rules were silently dropped on rebuild. **Fix:** moved `load_1120s_full` to
  `AMEND_LOADERS` (phase 3). Rebuild now reproduces 17/8 rules. **Zero prod change** — prod already had them.
- **§B / §D (8283/8949/8995/8995A double sets + bare-8582) — LOADER POLLUTION.** `load_1120s_complete`
  (`_load_8995/_load_8995a/_load_8582/_load_8283`) and `load_1120s_specs` (`_load_form_8949`) re-seeded
  1040-owned forms with a duplicate rule set (R001-R00x) prod never had, and fabricated a bare `8582`.
  **Fix:** removed those blocks. The 1040 primaries own the forms with correct multi-entity types.
  **Zero prod change** — prod was already clean; the pollution was rebuild-only.
- **§C-new (4797 v1 empty stub) — the last prod cruft.** Deleting 4797's orphan rules on 2026-07-04 left
  an emptied v1 version row (0 rules) that no loader reproduces (the export serves v2, 8 rules).
  **Fix:** deleted the v1 stub from prod (snapshot `remediation_snapshot_4797_v1.json`). Prod 93 → **92**.
- **BONUS (GA600S content, DECISIONS D-8):** the GA S-corp spec (`load_remaining_1120s`) carried a stale
  **5.49% PTET rate (live compute `* 0.0549`)** and a **3-factor apportionment formula** — both wrong for
  2025. Corrected to **5.19%** (Form 600S Rev. 09/11/25) and the **single gross-receipts factor**
  (§48-7-31), verified via the GA-700 research; reseeded to prod.

Loader fixes: commit `5f46311`. Verification method: `scratchpad/rebuild_diff.py` + a per-form rule_id diff
(`dump_rules.py`) — repeatable for the standing check (item 3 below).

---


*July Rule Studio checklist item: "fresh DB + all loaders + diff vs. production; document
result in RS STATUS (if anything lives only in Supabase → fix now)." This is the documented
result. Method: built a throwaway SQLite DB, ran every loader via the new `seed_all`
orchestrator, and diffed the rebuilt DB against production Supabase (form set, per-form rule
ids, and entity-model counts).*

## Verdict

**Production does NOT cleanly reproduce from the loaders in source control.** The rebuild is
close but not identical — there is real drift in four categories (below). Authority **sources
reproduce exactly** (0 delta across AuthoritySource/Excerpt/FormLink after the ordering fix).
The root cause is structural: **there was no canonical rebuild orchestrator**, and production
has been mutated incrementally for months and never verified against a from-scratch rebuild,
so it accumulated stale forms and orphaned legacy rules.

## What was fixed this session (code, zero prod risk)

- **`specs/management/commands/seed_all.py`** — the missing orchestrator. Runs all loaders in
  dependency order: sources → specs `load_*` → amend loaders → flow assertions. On a fresh DB
  it completes **61/61 loaders, 0 problems**. `--dry-run` prints the plan. Loaders are
  discovered dynamically so new ones are picked up; amend loaders are listed explicitly.
- This resolves the one **hard rebuild break**: `load_1040_form_3800` is an *amend* loader that
  refuses to create its base spec. In plain alphabetical order it ran before the 1120-S base
  3800 existed and raised `CommandError`. Running amends last (as `seed_all` does) → 3800
  rebuilds to the full 12 rules. Ordering-only; now encoded.

## Residual drift (needs a Ken call — all are production-data changes)

### A. Production carries orphaned legacy rules that no current loader reproduces (data lives only in Supabase)

The loaders for these forms were refactored to new `rule_id`s; production kept the OLD rule
rows (loaders use additive `update_or_create` and never delete). A from-scratch rebuild does
not reproduce them:

| Form | prod rules | rebuilt | prod-only rule_ids (orphaned) |
|---|---|---|---|
| `4797` | 17 | 8 | R001–R008, R010 (9) |
| `SCH_K_1120S` | 17 | 8 | R010–R018 (9) |
| `SCHD_1120S` | 8 | 5 | R010–R012 (3) |

→ **Decide:** if these are superseded by the refactor, delete the orphaned rule rows from prod
so it matches the clean rebuild. If any are still meaningful, they are unversioned data at
risk and the loader must be updated to reproduce them.

**SUPERSESSION ASSESSMENT (2026-07-04, read-only content diff — Ken chose "investigate first"):**

- **`4797` — SUPERSEDED, safe to delete.** The current loader produces the refactored `R-4797-*`
  set (CHARCLASS = §1245/§1250 by property character; ADDLDEPR = computed line 26a; 1231NET =
  5-yr lookback; RECAP; ROUTE; GAIN; ORD; PART4). The orphaned `R001–R010` are the *pre-refactor*
  naive version — holding-period routing, `min(gain, depr)` recapture, and **`R007` hardcodes
  §1250 recapture = 0**, the exact bug the 4797 nuance leg fixed (RS `03a5606`). Stale duplicates
  of superseded (and partly wrong) logic. → **DELETE the 9 orphaned rows from prod.**

- **`SCH_K_1120S` — NOT cleanly superseded, DO NOT blind-delete.** The current loader produces only
  8 high-level routing rules (ordinary / rental-8825 / capgain / §1231 / §179 / charitable / QBI /
  pro-rata base). The orphaned `R010–R018` include line-level detail the current loader **dropped**:
  `R011` interest, `R012` dividends (5a/5b), `R016` nondeductible meals, `R017` total distributions,
  `R018` K18 income/loss reconciliation — none of which appear in the fresh set. `R010/R013/R014/R015`
  (K1←Page1, K7/K8a←Sch D, K9←4797) overlap the fresh routing. → **DO NOT delete. This is dropped
  detail — the current 1120-S loader regressed vs the earlier richer version.** Fold into the
  **August "1120-S delta audit"** (already on the checklist).

- **`SCHD_1120S` — borderline.** `R011/R012` (Sch D Part I L5 → K7, Part II L12 → K8a) overlap the
  fresh `R004` "flow to Schedule K"; `R010` (validation: Sch D excludes §1231) is unique and worth
  keeping. → **Hold with SCH_K_1120S in the 1120-S delta audit; do not delete piecemeal.**

**Net:** only the `4797` orphans are confirmed safe to delete. The `SCH_K_1120S` / `SCHD_1120S`
orphans surface a real regression in the 1120-S family loaders (line detail present in prod, absent
from the current loaders) — this is exactly what the August 1120-S delta audit is for; deleting them
now would destroy data the audit needs.

### B. Production is stale — current loaders produce newer rules prod doesn't have

| Form | prod rules | rebuilt | new rule_ids the loader adds |
|---|---|---|---|
| `8283` | 5 | 10 | R001–R005 (5) |
| `8949` | 5 | 9 | R001–R004 (4) |
| `8995` | 9 | 14 | (5) |
| `8995A` | 11 | 17 | (6) |

**INVESTIGATED 2026-07-04:** prod **exactly matches the 1040 primary loaders** for all four
(`load_1040_form_8283`→5, `load_1040_schedule_d`→5, `load_1040_schedule_c`→9,
`load_1040_form_8995a`→11 — all MATCH prod). The extra rules in a full rebuild come **entirely
from `load_1120s_complete` / `load_1120s_specs`**, which add a *second* rule set to these forms.
So this is NOT a clean isolated re-seed — it is entangled with the 1120-S loader family (same
loaders behind A and D). → **Fold into the August 1120-S delta audit**, not a quick prod re-seed.

### C. Cruft — a form that lives only in the DB

- **`1065`** — an empty stub: `entity_types=[]`, 0 rules, and its `form_title` is mislabeled
  "1065_SE". No loader creates it. The real partnership forms are `1065_PAGE1`, `SCH_K_1065`,
  `1065_L/B/M1/M2`, `SCHEDULE_K1_1065`, `1065_SE`. → **Decide:** delete the stub from prod.

### D. Spurious `8582` duplicate from the 1120-S loader (was misdiagnosed as naming drift)

**CORRECTED 2026-07-04:** `FORM_8582` (12 rules, `entity=['1040']`) is the **legitimate**
Passive Activity Loss form — created by its proper loader and referenced by the 4835 spec
("the EXISTING FORM_8582 spec"). It is correct in prod. The reconstructability "fresh-only
`8582`" is a **separate, spurious bare-`8582` stub (6 rules) that `load_1120s_complete`
creates** — it never existed in prod. So this is NOT a prod naming problem; it's a **code bug
in `load_1120s_complete`** (it fabricates a duplicate 8582). → **Fix in the August 1120-S delta
audit** (stop the 1120-S loader creating the duplicate). Do NOT rename `FORM_8582`.
*(An initial rename of `FORM_8582`→`8582` was executed and immediately reverted once the diff
revealed both forms exist in the rebuild — see "Executed" below.)*

## Count snapshot (prod → rebuilt, `seed_all` order)

```
TaxForm            89 -> 88   (-1: the 1065 stub)
FormRule          759 -> 764  (net +5: +20 from stale forms B, -21 orphans A, 3800 restored)
FormLine         2450 -> 2445
FormDiagnostic    529 -> 535
TestScenario      711 -> 716
FlowAssertion     420 -> 421
AuthoritySource   299 -> 299  (exact match)
AuthorityExcerpt  756 -> 723  (excerpts on the orphaned/stale forms; tracks A/B)
AuthorityFormLink 431 -> 414
```

## Executed remediation — 2026-07-04 (Ken: "do all safe items")

Snapshot-backed, transactional, against prod (`remediation_snapshot.json` holds the backup):

- ✅ **Deleted the 9 `4797` orphan rules** (R001–R008, R010; + 13 cascaded authority links =
  22 objects). Prod `4797` now = 8 rules, matching the loader. Confirmed superseded (§A).
- ✅ **Deleted the `1065` empty stub** (entity=[], mislabeled "1065_SE"; + 2 cascaded FormLines).
  `TaxForm` 89 → **88**. No loader creates it; not reproducible = correct to remove.
- ↩️ **Reverted a mistaken `FORM_8582`→`8582` rename.** The re-diff showed the rebuild produces
  BOTH `FORM_8582` (real) and a spurious bare `8582` (§D) — so `FORM_8582` was correct all along.
  Renamed back immediately; `FORM_8582` (12 rules) intact.
- ⏸ **Deferred to the August 1120-S delta audit:** the stale forms (B), the SCH_K_1120S/SCHD_1120S
  orphans (A), and the spurious bare-`8582` loader duplicate (D) — all trace to
  `load_1120s_complete/specs` and must be adjudicated together, not piecemeal.

**Post-remediation diff:** the only residual prod↔rebuild deltas are the 1120-S-loader items above.
`1065` and `4797` are resolved (0 delta); **authority sources match exactly**.

## Remaining remediation order

1. ✅ **Done:** `seed_all` orchestrator committed; 4797 orphans + 1065 stub removed from prod.
2. ✅ **Done 2026-07-05 (the August 1120-S delta audit — see the banner at top):** the ordering bug
   (`load_1120s_full` → `AMEND_LOADERS`), the pollution removal (8283/8949/8995/8995A/bare-8582), the
   4797 v1 stub deletion, and the GA600S 5.49%/3-factor correction. **prod ↔ rebuild = 0-delta.**
3. **Standing:** run `seed_all` on a fresh DB + the rule_id diff (`scratchpad/rebuild_diff.py` +
   `dump_rules.py`) periodically so prod never silently drifts from source control again.
