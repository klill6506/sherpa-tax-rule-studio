# CHANGE_REGISTER.md — the tax-law-change funnel (front-of-the-front-door)

*Adopted 2026-07-08. This is the TRIGGER that feeds `WORK_ORDERS.md` INTAKE. It closes the loop
CLAUDE.md and WORK_ORDERS.md always anticipated: **a law change → a new tax rule (RS spec) → a
tax-app change (tts build)**. Before this, net-new RS scope entered only when Ken named a form or a
form-usage report surfaced one. Now a law change is a first-class, tracked trigger.*

***This register does NOT bypass the two gates.** A change can START a draft; nothing CROSSES a gate
unattended. Gate 1 = draft→published spec (Ken). Gate 2 = published→compute (the existing tts ingest).
A promoted change becomes a WORK_ORDERS order and then runs the SAME front door as every other form.*

---

## The funnel

```
  DETECT ───────────────► TRIAGE ────────────────► PROMOTE ──────────► WORK_ORDERS.md INTAKE
  a source moved           ChangeRegisterItem        opens a WO           (the existing front door)
  · manual clip (Ken)      · affected forms?         · --work-order WO-NN  gap-check → research-verify
  · checksum diff          · which tax year?         · status = PROMOTED   → Gate-1 scope walk (Ken)
    (detect_source_        · substantive?                                  → author READY_TO_SEED=False
     changes)              status: DETECTED →                              → SQLite-validate → seed
                           TRIAGED → PROMOTED/                             → export → tts [APP] build
                           DISMISSED                                        ⟨Gate 2: tts ingest⟩
```

**Two arms into DETECT (both live as of 2026-07-08):**
- **Manual clip** — Ken (or CC on a known law change) records it:
  `manage.py change_register add --title "..." --summary "..." --forms 3115 --tax-year 2026 --source REVPROC_2025_23`
- **Checksum diff** — re-fetch checksums, diff against each source's current `AuthorityVersion`:
  `manage.py detect_source_changes --manifest scratchpad/latest_checksums.json`
  (opens a `DETECTED` item per moved source; idempotent; flags sources with no current version as a
  feed-coverage gap. Network fetching itself is the FEED_POLL follow-up — v1 diffs supplied checksums.)

## Status lifecycle (the `ChangeRegisterItem` model, `sources` app)
`DETECTED → TRIAGED → PROMOTED` (or `→ DISMISSED`). Backed by a DB model (queryable, FKs to
`AuthoritySource` / `AuthorityVersion` / `SourceFeedDefinition`) AND this human-readable ledger.
Update this file at each transition, same discipline as WORK_ORDERS.md.

## Commands
| Step | Command |
|---|---|
| record | `change_register add --title T --summary S [--forms a,b] [--tax-year Y] [--jurisdiction US] [--source CODE]` |
| triage | `change_register triage --code CR-YYYY-NNN --substantive|--not-substantive [--forms a,b] [--rules r1,r2] [--notes N]` |
| promote | `change_register promote --code CR-YYYY-NNN --work-order WO-NN` |
| dismiss | `change_register dismiss --code CR-YYYY-NNN --notes N` |
| list | `change_register list [--status detected]` |
| detect | `detect_source_changes --manifest <json> | --from-files [--dry-run]` |

## What feeds it (design intent — see [[rs-change-register-funnel]])
- IRS IRB / Rev. Proc. / Notice releases (the annual automatic-change list, indexed-amount updates).
- Statute changes (OBBBA-style: P.L. amendments to the Code).
- State DOR conformity + form updates (GA/SC/AL/NC — via `JurisdictionConformitySource`).
- `SourceFeedDefinition` rows describe WHERE to look; `detect_source_changes` diffs WHAT moved.

## Deferred (not in v1, by Ken's 2026-07-08 scoping)
- **Staleness auto-flag** (Authoritative-Source Rule step 5): when a source moves, auto-mark the
  dependent `FormRule`s (via `RuleAuthorityLink`) as stale. v1 opens a change item but does not touch
  rules. Follow-up: a `stale_rules_report` that lists the blast radius of a promoted change.
- **FEED_POLL**: the network fetchers/parsers per `SourceFeedDefinition` that would auto-produce the
  checksum manifest `detect_source_changes` consumes.
- **REST API** for the register (consistent with `/api/sources/…`) — CLI + this doc are the v1 front door.

---

## ▶ OPEN ITEMS
*None yet — the register is live and empty. The first real trigger (a law change or a checksum diff)
records here. When the S-16 queue drained (2026-07-06), this funnel became the primary way net-new RS
authoring scope enters.*

| Code | Status | TY | Forms | Title | → WO |
|---|---|---|---|---|---|
| _(none)_ | | | | | |

## ✅ PROMOTED / DISMISSED (history)
*(empty)*

---

## Maintenance
- Lives in the RS repo root (like WORK_ORDERS.md); on the CC boot list. Mirrored to the public
  `tts-tax-status` status repo on session close — keep PII/sensitive prose out.
- The model is `sources.ChangeRegisterItem`; the commands are `change_register` + `detect_source_changes`.
