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

**Three arms into DETECT (all live):**
- **Manual clip** — Ken (or CC on a known law change) records it:
  `manage.py change_register add --title "..." --summary "..." --forms 3115 --tax-year 2026 --source REVPROC_2025_23`
- **Checksum diff** — re-fetch checksums, diff against each source's current `AuthorityVersion`:
  `manage.py detect_source_changes --manifest scratchpad/latest_checksums.json`
  (opens a `DETECTED` item per moved source; idempotent; flags sources with no current version as a
  feed-coverage gap. v1 diffs supplied checksums; the fetcher that produces the manifest is future work.)
- **Federal Register poll (FEED_POLL leg 1, BUILT 2026-07-08)** — auto-discovers recent IRS/Treasury
  regulatory documents from the free Federal Register API:
  `manage.py fetch_federal_register [--since YYYY-MM-DD | --lookback-days N] [--types RULE,PRORULE,NOTICE] [--dry-run]`
  (opens a `DETECTED` `feed_poll` item per new final/proposed rule; idempotent by FR `document_number`
  stored in `external_ref`; stdlib urllib, no key. ⚠ The FR carries REGULATIONS — sub-regulatory guidance
  (Rev. Procs/Notices/Rulings, e.g. the annual automatic-change list) publishes in the IRB, not the FR,
  so those still arrive via manual clip / a future IRB leg.)

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
| detect (checksum) | `detect_source_changes --manifest <json> | --from-files [--dry-run]` |
| detect (Fed. Register) | `fetch_federal_register [--since YYYY-MM-DD | --lookback-days N] [--types ...] [--dry-run]` |

## What feeds it (design intent — see [[rs-change-register-funnel]])
- IRS IRB / Rev. Proc. / Notice releases (the annual automatic-change list, indexed-amount updates).
- Statute changes (OBBBA-style: P.L. amendments to the Code).
- State DOR conformity + form updates (GA/SC/AL/NC — via `JurisdictionConformitySource`).
- `SourceFeedDefinition` rows describe WHERE to look; `detect_source_changes` diffs WHAT moved.

## Deferred / follow-ups
- **Staleness auto-flag** (Authoritative-Source Rule step 5): when a source moves, auto-mark the
  dependent `FormRule`s (via `RuleAuthorityLink`) as stale. v1 opens a change item but does not touch
  rules. Follow-up: a `stale_rules_report` that lists the blast radius of a promoted change.
- **FEED_POLL leg 2+**: the **IRB** feed (Rev. Procs / Notices / Rulings — where sub-regulatory guidance
  lives) and **Congress.gov** (statutes / P.L.); a fetcher that produces the `detect_source_changes`
  checksum manifest for form/pub revisions. (Leg 1 = Federal Register regulations, BUILT 2026-07-08.)
- **Scheduling**: a recurring job (Render cron or a scheduled CC routine) that runs `fetch_federal_register`
  weekly so regulatory changes flow in unattended. Currently run on demand in a session.
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
