---
type: project-memory
project: sherpa-tax-rule-studio
last_updated: 2026-07-04
---

# MEMORY — sherpa-tax-rule-studio

*Standing facts, preferences, and accumulated context. Long-lived — not "what I did yesterday" (that's STATUS.md). Update when you learn something worth keeping.*

---

## Purpose and scope

<Why this app exists, who uses it, what problem it solves. 2-3 sentences max.>

## Domain knowledge

<Rules of the domain that Claude should know before making changes. For tax apps: the specific IRS rules this module implements, state conformity notes, edge cases. For non-tax apps: business rules, workflows, naming conventions specific to this app's world.>

## User preferences discovered

<Things Ken has said he prefers, or patterns that work / don't work. Example: "Ken prefers server-rendered HTML over SPAs for internal tools." "Don't auto-format tax return numbers with commas on input, only on display.">

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

## Data model highlights

<Key tables/models and what's non-obvious about them. Don't duplicate the schema — reference it. Focus on the things you'd warn someone about.>
