---
type: project-memory
project: sherpa-tax-rule-studio
last_updated: 2026-07-06
---

# MEMORY — sherpa-tax-rule-studio

*Standing facts, preferences, and accumulated context. Long-lived — not "what I did yesterday" (that's STATUS.md). Update when you learn something worth keeping.*

---

## Purpose and scope

RS is a standalone tax-law spec-authoring tool (NOT a tax-prep app). Ken (CPA) authors structured,
machine-readable, cited-and-versioned rule packages here; the JSON export is handed to coding agents that
implement the compute in tts-tax-app. A spec is a test oracle, not runtime data.

## Domain knowledge

**The front-door authoring pattern (standardized, battle-tested across the S-16 federal-forms queue — WO-14
through WO-23, ALL 10 forms, 2026-07-05/06; the S-16 queue is now FULLY DRAINED. Next RS scope needs the
TaxWise forms-usage report or a law change — there is no queued next order).** Each form ran the same loop,
one form per Work Order:
1. **Gap-check** — `GET /api/forms/lookup/<FORM>/export/` (via Django test client, set
   `settings.ALLOWED_HOSTS=['testserver']`); 404 = GAP, 200 = already exists. Open a WO in WORK_ORDERS.md.
2. **Research** — spawn a subagent to verify VERBATIM against the FINAL IRS source (form + instructions +
   statute). NEVER author from memory. It routinely CATCHES errors (e.g., 709 applicable credit was
   $5,541,800 not the 2024 $5,389,800; Sch H trigger $2,800 not $2,700). Write `f<form>_source_brief.md`.
3. **Gate-1 scope walk** — 3-4 AskUserQuestion, recommended option FIRST in each; record as a DECISIONS
   D-## entry. Ken approves compute-vs-defer.
4. **Author** `load_<form>.py` with **`READY_TO_SEED=False`** (a guard that refuses to seed) + a validation
   harness `scratchpad/validate_<form>.py` (throwaway SQLite; arithmetic/logic oracles for every scenario).
5. **Gate-1 seed approval** — present the W1-Wn review walk, Ken says "Approve — flip, seed, export".
6. Flip guard True → `manage.py load_<form>` (seeds prod Supabase) → verify export=200 → `seed_all
   --dry-run` shows `load_<form>` (reconstructable) → commit + push both repos → update WORK_ORDERS /
   BUILD_ORDER / STATUS / DECISIONS.

**Loader shape:** copy the newest loader as the template (they share the Command boilerplate:
`_load_topics/_load_sources/_upsert_*`). Constants year-keyed at the top; pure helper functions for the
math (so the validate harness can call them directly); FACTS / RULES / RULE_LINKS / LINES / DIAGNOSTICS /
SCENARIOS / FLOW_ASSERTIONS lists; every rule needs >=1 authority link (all cited).

**Conventions that matter:** year-key EVERY indexed constant + note re-verify each season (OBBBA repeatedly
moves things — e.g. 8839 refundability, 709 $15M BEA is 2026-not-2025). Flag anything the source doesn't
confirm as **[UNVERIFIED]** rather than guessing (709 carried unverified line #s when the raw PDF face
wouldn't fetch; matches the NC/AL line-# precedent). Cite a relationship to its real authority, not a
convenient one (8814→8615 cited to §1(g)/Pub 929, not i8814, because i8814 doesn't mention it).

**Form-number lookup** is `form_number__iexact` with no FORM_ stripping — seed numbered forms under the
bare number (`4952`, `709`), schedules under `SCHEDULE_H` style. entity_types tags which returns a form
serves (e.g. 8832 = [1065,1120,1120S,1040]; 709 = its own [709]).

## User preferences discovered

- **Ken drives the queue with "go" / "run it" / "continue"** and approves each form's scope + seed via the
  two AskUserQuestion gates. He nearly always takes the RECOMMENDED option — so lead with a well-reasoned
  recommendation, not an even menu.
- **Commit + push both repos after every form** (RS + the BUILD_ORDER tick in tts-tax-status). Use
  explicit-path `git add`, never `git add -A` (a parallel session shares the working tree).

## Integrations and external systems

- **Public status mirror (added 2026-07-04):** RS `STATUS.md` and `session_log.md` are auto-copied into
  the **public** GitHub repo `klill6506/tts-tax-status` (under a `rule-studio/` subfolder) by
  `tts-tax-app/scripts/sync_status_mirror.ps1` at session close. The RS repo itself is going private, so
  this mirror is how RS status stays visible. `tts-tax-app` is the source of truth for the mirror's root
  files; RS is the source for the `rule-studio/` ones. **Never hand-edit the `D:\dev\tts-tax-status`
  clone** — the script overwrites it on every run.

## Gotchas and lessons learned

- **RS status files are PUBLIC.** Because of the mirror above, anything written to `STATUS.md` or
  `session_log.md` lands in a public repo. The sync's PII guard only blocks SSN-shaped values and EFIN
  mentions — it does NOT catch sensitive prose (client names, firm strategy, bank/entity specifics).
  Keep those out of the two mirrored files.
- **`BUILD_ORDER.md` in `D:\dev\tts-tax-status` IS directly edited** (unlike the auto-synced `rule-studio/`
  STATUS mirror). It's the shared order ledger both CC contexts write; ticking S-16 items there and pushing
  works fine alongside the parallel tts session's edits. Don't confuse it with the mirror files the sync
  script overwrites.
- **CharField caps (Postgres enforces what SQLite ignores):** `rule_id` / `diagnostic_id` / `assertion_id`
  / `line_number` <= 20; `topic_name` <= 255; `fact_key` <= 100. The validate harness checks these. The
  `topic_name` 255 cap bit ~every form this session — keep the AuthorityTopic name terse from the start.
- The BEA/gift constants: 709 applicable credit = tentative tax on the BEA ($5,541,800 for 2025). OBBBA's
  $15M BEA and estate/gift changes are **2026+**, not 2025 — year-key so they can't leak into a 2025 return.

## Data model highlights

- **Reconstructability is the contract:** prod Supabase must rebuild from the loaders. `seed_all`
  auto-discovers `load_*.py` (verify with `seed_all --dry-run` after seeding a new form). Never let state
  live only in Supabase — approvals go in `specs/approved_specs.py` (applied by `approve_specs`, a seed_all
  phase), not a DB edit. Each form: `TaxForm` + child `FormFact`/`FormRule`/`FormLine`/`FormDiagnostic`/
  `TestScenario` + `FlowAssertion`; authority via `AuthoritySource`/`AuthorityExcerpt` + `RuleAuthorityLink`
  (join table — a rule with zero links shows a warning badge).
