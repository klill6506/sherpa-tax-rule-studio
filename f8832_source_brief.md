# Source Brief — Form 8832, Entity Classification Election ("check-the-box")

**WO-22 · SPINE S-16 (9th item) · greenfield RS-first**
Research pass 2026-07-06, verbatim vs current FINAL Form 8832 (Rev. 12-2013) + §301.7701-3. Nothing [UNVERIFIED].

---

## Sources

| source_code | title | citation |
|---|---|---|
| `IRS_F8832` | Form 8832 — Entity Classification Election | Form 8832 (**Rev. December 2013**), Cat. No. 22598R, OMB 1545-1516 (current — no annual reissue; face + instructions pp. 4-7) |
| `REG_7701_3` | Treas. Reg. §301.7701-3 — classification of eligible entities (check-the-box) | 26 CFR §301.7701-3(b)/(c) |
| `REVPROC_2009_41` | Rev. Proc. 2009-41 — late entity-classification election relief | Rev. Proc. 2009-41 (3-years-75-days relief) |

---

## What this is

An **eligible entity** uses Form 8832 to ELECT its federal tax classification (§301.7701-3): a domestic eligible entity
elects to be **(1) an association taxable as a corporation, (2) a partnership, or (3) disregarded** as separate from its
owner (single owner only); three foreign equivalents. If it does NOT file, it takes its **default** classification. A
**per-se corporation** (a state-law corporation, §301.7701-2(b)) is NOT an eligible entity and cannot elect. Distinct
from **Form 2553** (S-election, which is deemed to also elect association/corporation status — no separate 8832).

---

## The form face (verbatim line map, Rev. 12-2013)

**Top boxes:** address change · **late classification relief (Rev. Proc. 2009-41)** · relief for a late change (Rev.
Proc. 2010-32).

**Part I — Election Information**
- **L1 type of election:** **1a** initial classification by a newly-formed entity (skip 2a/2b → L3) · **1b** change in
  current classification (→ 2a).
- **L2a** previously filed an election effective within the last **60 months**? Yes → 2b; No → skip to L3.
- **L2b** was the prior election an initial classification by a newly-formed entity effective on the formation date?
  Yes → L3; **No → STOP (generally not currently eligible — the 60-month rule).**
- **L3** more than one owner? **Yes → partnership or association-taxable-as-corp** (skip L4 → L5); **No → corp or
  disregarded** (→ L4).
- **L4** single owner name (4a) / identifying number (4b). **L5** affiliated-consolidated parent name (5a) / EIN (5b).
- **L6 type of entity** — six checkboxes: **6a** domestic → association taxable as a corp · **6b** domestic →
  partnership · **6c** domestic single-owner → disregarded · **6d/6e/6f** the foreign equivalents.
- **L7** foreign country of organization · **L8 effective date** · L9/L10 contact person + phone. Consent + signatures.

**Part II — Late Election Relief** — **L11** explanation why not filed on time; the Rev. Proc. 2009-41 §4.01 declaration.

---

## Key rules (for compute/diagnostics — verbatim substance)

- **Default classification (§301.7701-3(b)):** domestic **2+ members → partnership**; domestic **1 member → disregarded**.
  Foreign: 2+ and at least one member without limited liability → partnership; **all members have limited liability →
  association (corp)**; single member without limited liability → disregarded. *TIP: a new entity using its default
  should NOT file 8832.*
- **60-month limitation (§301.7701-3(c)(1)(iv)):** once an eligible entity elects to CHANGE its classification, it
  generally cannot change again for **60 months** after the effective date. Exceptions: a >50% ownership change (by
  PLR); and it does NOT apply where the prior election was a newly-formed entity's initial election effective on formation.
- **Effective-date window (L8):** the election can take effect **no more than 75 days BEFORE** the filing date and **no
  later than 12 months AFTER**. Outside → it defaults to the boundary (75 days before / 12 months after); blank → the
  filing date.
- **Late relief (Rev. Proc. 2009-41):** available if the entity failed to get the classification solely because 8832
  wasn't timely filed, meets the return-consistency condition, has **reasonable cause**, and **3 years and 75 days**
  from the requested effective date have NOT passed. Otherwise → private letter ruling.
- **Form 2553 boundary:** an entity electing S-corp status files **Form 2553** (deemed §301.7701-3(c)(1)(v) association
  election) — do NOT file 8832 for an S-election.
- **Where to file / attach:** file with the IRS service center + **attach a copy to the entity's (and owners') return**
  for the election year. **Updated addresses (supersede the printed instructions): Kansas City, MO 64999 / Ogden, UT
  84201 / Ogden, UT 84201-0023.**

## Recent changes

**None.** Rev. 12-2013 is current; **no OBBBA impact** (structural §7701 election, not rate-driven). The only post-2013
update is the prepended new-mailing-address page.

---

## Proposed scope for the Gate-1 walk (compute vs defer)

1. **Part I eligibility + classification decision tree** — compute the L1→L3 routing → an `is_eligible_to_elect`
   determination (the 60-month gate at L2a/L2b; per-se corp ineligible) + the available classifications (multi-owner →
   partnership/corp; single-owner → corp/disregarded) + the L6 election type. Stop-reason diagnostics.
2. **Default classification rules** — compute the default (domestic 2+ → partnership, 1 → disregarded; foreign by
   limited liability) + the "don't file if using the default" TIP.
3. **Effective-date window + 60-month + late relief** — the 75-days-before / 12-months-after window (+ clamp behavior);
   the 60-month limitation gate; the Rev. Proc. 2009-41 late-relief diagnostic (3 years 75 days + reasonable cause).
4. **Form 2553 boundary + filing + scope** — diagnostics for the 2553 boundary (S-election → 2553), per-se-corp
   ineligibility, the attach-to-return rule + the updated Kansas City/Ogden addresses; one `8832` form, entity_types
   = the classifications it touches (1065 / 1120 / 1120S / 1040-disregarded).
