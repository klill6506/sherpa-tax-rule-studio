# RS DB Reconstructability Check — 2026-07-04

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

→ **Safe/additive:** re-seed these in prod (e.g. `seed_all`, or the individual loaders) to
catch prod up to source control. No data loss.

### C. Cruft — a form that lives only in the DB

- **`1065`** — an empty stub: `entity_types=[]`, 0 rules, and its `form_title` is mislabeled
  "1065_SE". No loader creates it. The real partnership forms are `1065_PAGE1`, `SCH_K_1065`,
  `1065_L/B/M1/M2`, `SCHEDULE_K1_1065`, `1065_SE`. → **Decide:** delete the stub from prod.

### D. Form-number naming drift

- Production has **`FORM_8582`** (legacy prefixed name, `entity=['1040']`). The current loader
  emits bare **`8582`**, per the established bare-number convention (cf. `6198`, `4835`). A
  re-seed would create `8582` and leave `FORM_8582` orphaned. → **Decide:** rename the prod row
  `FORM_8582` → `8582` (and confirm nothing references the old key), converging on the loader.

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

## Recommended remediation order

1. ✅ **Done:** `seed_all` orchestrator committed (fixes ordering + gives a repeatable rebuild).
2. **Ken call — prod cleanup (deletions):** drop the `1065` stub (C); drop orphaned legacy rules
   on 4797 / SCH_K_1120S / SCHD_1120S (A) once confirmed superseded; rename `FORM_8582`→`8582` (D).
3. **Ken call — prod re-seed (additive):** run `seed_all` against prod to catch up the stale
   forms (B). Idempotent; brings prod up to the loaders but does not remove orphans (do step 2 first).
4. **Re-run this check** after remediation; target a clean 0-delta rebuild (modulo intended prod-only).
5. **Standing:** wire `seed_all --dry-run` (or a periodic full rebuild+diff) into the season
   cadence so prod never silently drifts from source control again.
