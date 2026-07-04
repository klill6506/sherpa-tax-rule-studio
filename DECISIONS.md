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
