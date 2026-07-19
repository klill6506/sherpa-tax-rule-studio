## 2026-07-19 - 1065_B Q4 auto-answer amendment (S-21c spec leg; tts s99) - SEEDED + tts leg SHIPPED
- Amended IN THE OWNING LOADER (load_1065_l_b.py, single-entity 1065_B - in-place re-run safe;
  `7a55f57`): NEW R-B4-AUTO - the app derives Q4 as derived-YELLOW/overridable: 4a = receipts
  < $250K STRICT per the i1065 (2025) Q4 verbatim sum (p1 1a; p1 4-7; K 3a/5/6a/7;
  income-or-net-gain K 8/9a/10/11; 8825 2/21/22a; positive-only, the 1120S R006 interpretive
  mirror) - 4b = item F (Sch L 14(d), app L15d) < $1M STRICT - 4c PRESUMED TRUE (Ken-ratified) -
  4d derived TRUE under 4a·4b (tts prepares no M-3; item-J thresholds unreachable; the
  reportable-entity-partner edge rides the preparer override - RULING DEVIATION flagged, tts
  REVIEW_QUEUE s99a). B-6/B-7 boundary scenarios added (strict-< at exactly $250K; the derived-Yes
  shape). Stale "build-gap #3" text CLOSED across R-B4-SMALL / D_B4_SMALL / GATE-SMALL-PTNR-B
  (the tts gate has been live since the L/B unit; now the answer derives too).
- Reseeded + deployed export verified (6 rules / 7 scenarios / line 4 dual-ruled); tts 1065 FA
  mirror refreshed export-minus-pending (39; the 4 s64-staged ids stay pending).
- tts leg landed same-session (`b7f77b6`): _auto_answer_b6_1065_db after the 1065 formula pass;
  face-verbatim B6 label reseeded BOTH DBs; Auto pill scoped (1120-S,B11)+(1065,B6);
  test_1065_schb_q4 7/7; flow 518; live demo probe green.
- FOUND: the tts sched_b block is a stale pre-face paraphrase (non-face B2/B5; missing
  Q24/Q30/Q33) - the face-renumber filed as its own queued unit (tts REVIEW_QUEUE s99b).

## 2026-07-15 - WO-33 (8879/8878 signature-authorization pair) DRAFTED TO GATE-1 - AWAITING KEN (tts s90)
- Gap 404 x4 confirmed (8879/FORM_8879/8878/FORM_8878); verbatim research: f8879 Rev. 01-2021
  (continuous-use) + f8878 (2025, YEAR-DATED) + Pub 1345 signature chapter + the 2025v5.3 header
  XSDs + 47 signature-family business rules -> f8879_8878_source_brief.md.
- NEITHER FORM TRANSMITS (ERO-retained; no MeF document BY DESIGN - the Return Header PIN block
  tts already e-files is the electronic signature). The tts leg on approval = signature-input
  surface + two AcroForm prints + header-tie diagnostics + extract gating (the s87 print-only
  recipe, header tie instead of payment tie).
- Headline catches: the 8879 4-row chart collapses to PP-method-OR-ERO-entered (PP + own-PIN
  STILL requires the full form incl. Part III - Pub 1345 always-sign); the 8878 no-EFW-never
  negative (the s88 R0000-098 print mirror); 2350 never reaches Part III; the Pub-1345 $50/$14
  re-sign tolerance (needs a signed-at Part I snapshot); 3-day stockpiling clock; the under-16 +
  duplicate-SSN self-select bars; the year-dated 8878 face (year-watch).
- load_8879_8878.py authored GATED (READY_TO_SEED=False): one loader, two TaxForms - 22+14 facts /
  8+4 rules / 16+13 lines / 9+7 diagnostics / 8+6 scenarios / 3 FAs staged DRAFT. Harness
  scratchpad/validate_8879_8878.py = 77/0 (guard-refusal + twice-run + all nine chart rows +
  tolerance boundaries + scenario recomputes + flagged-seam presence + ASCII pin).
- WORK_ORDERS WO-33 filed AWAITING KEN with the W1-W4 walk (recommend approve-all; four seams
  flagged w/ recommendations: 8879 L3 = 25d, the 1040-X column-C arm, extract-refusal gating,
  the signed-at snapshot). NOT seeded, NOT exported, no tts code.

## 2026-07-15 — WO-32 (8915-F) DONE — tts s89 build leg landed; the three FAs ACTIVATED; THE SIX-LEG DISPATCH SET IS COMPLETE
- The tts unit shipped (Form8915F + Form8915FDisaster migs 0204/0205 BOTH DBs + compute_8915f pinned
  to all 10 spec oracles — the 179/180-day one-day asymmetry pinned both directions against every
  published date example incl. the SECURE-floor arm; the 1a-1e ladder + the Rev-12-2025 5a/5b split;
  the sequential-fill (b)-column allocation; whole-dollar ROUND_HALF_UP adopted for the flagged /3.0
  convention — tts REVIEW_QUEUE s89 ratification note) + 15 D_8915F_* diagnostics + the f8915f
  Rev-12-2025 AcroForm print (per-owner per-year copies; the lines-1-5 table SHADING-PROBED: 1a-1e
  fill column (b), 5a fills column (a)) + the IRS8915F MeF document (ReturnData1040 slot 2014 between
  IRS8912 and IRS8917, maxOccurs=6; live-XSD valid with TWO documents — the separate-spouse shape)
  + the 4b/5b landing moves + the 8606 15a/15b/25a/25b face split (owner_lines gained the QDD ties)
  + the 5329 line-6 waiver seam (owner_inputs suppresses the early-tax base).
- **FA-8915F-CAP/SPRD/LAND flipped draft → active in `load_8915f.py` + reseeded to prod**; deployed
  1040 FA export verified = 413 active (410 prior + 3); tts mirror refreshed export-verbatim
  (412 = 413 − the s71-staged FA-1040-4835-06); tts runners `_run_8915f_assertion` live in BOTH
  dispatch chains; tts flow gate 512 → 515.
- WORK_ORDERS WO-32 → ✅ DONE. **All six dispatched legs (WO-28/29/30/31/32) are now built.**

﻿# Rule Studio â€” Session Log
## 2026-07-15 — WO-31 (4868) DONE — tts s88 build leg landed; the three FAs ACTIVATED
- The tts unit shipped (Form4868 singleton migs 0202/0203 + compute_4868 pinned to all 10 spec
  oracles — both where-to-file columns partition-pinned, the FOUR-way GA Charlotte trap
  cross-module-pinned (V 1214 / ES 1300 / 4868 1302 / foreign 1303) + 16 D_4868_* diagnostics +
  f4868 AcroForm face render (suppression IS the render gate — a recorded e-payment confirmation
  = IND-900 territory; STANDALONE, never in the packet per the face's own instruction) + **the
  NEW extension SUBMISSION FAMILY** (Return4868/ReturnHeader4868/ReturnData4868 builder +
  read-model + Mapper4868TY2025; the no-payment-no-signature story + the two-value jurat ladder
  encoded; the FPYMT-052-02 tie holds by construction; live-XSD valid both shapes vs the local
  2026v1.0 Extensions tree) + the R-4868-CREDIT Sch 3 L10 YELLOW feeder (component-sum L5 derive
  — the subtract-from-line-33 form diverges under an override; caught by test) + the
  Payments-tab card, PATCH row-locked from birth).
- **FA-4868-L6/FA-4868-EFW/FA-4868-CREDIT flipped draft → active in `load_4868.py` + reseeded
  to prod**; deployed 1040 FA export verified = 410 active (407 prior + 3); tts mirror refreshed
  export-verbatim (409 = 410 − the s71-staged FA-1040-4835-06); tts runners
  `_run_4868_assertion` live in BOTH dispatch chains; tts flow gate 509 → 512.
- WORK_ORDERS WO-31 → ✅ DONE. Remaining dispatched set: 8915-F (WO-32, the last leg).

## 2026-07-15 — WO-30 (1040-V/ES pair) DONE — tts s87 build leg landed; the three FAs ACTIVATED
- The tts unit shipped (PaymentVouchers singleton migs 0200/0201 + compute_vouchers pinned to
  all 10 spec oracles — both mailing charts partition-pinned (the GA 1214-vs-1300 trap live-probed
  on a KY demo return: V→931000 / ES→931100) + 15 D_V_*/D_ES_* diagnostics + f1040v/f1040es
  AcroForm print legs (suppression IS the render gate; ES emits only the sheets carrying an
  emitted quarter) + the packet "voucher" back tier + the Payments-tab card, PATCH row-locked
  from birth).
- **FA-1040V-EFW/FA-ES-RAP/FA-ES-QDEBIT flipped draft → active in `load_1040v_es.py` + reseeded
  to prod**; deployed 1040 FA export verified = 407 active (404 prior + 3); tts mirror refreshed
  export-verbatim (406 = 407 − the s71-staged FA-1040-4835-06); tts runners
  `_run_1040ves_assertion` live in BOTH dispatch chains; tts flow gate 506 → 509.
- WORK_ORDERS WO-30 → ✅ DONE. Remaining dispatched set: 4868 → 8915-F.

## 2026-07-14 — WO-29 (8888) DONE — tts s86 build leg landed; the three FAs ACTIVATED
- The tts unit shipped (Form8888 singleton mig 0198 + compute_8888 pinned to the spec
  scenarios (two-way tie / hygiene / the Active F8888-* gate verbatim) + 12 D_8888_*
  diagnostics + f8888 Rev-12-2025 AcroForm print (face page only; line 4 unmapped) + the
  IRS8888 MeF document (Form8888Ind + IND-084 suppression + per-account header
  RefundDisbursementGrp fan-out) + the Payments-tab card).
- **FA-8888-TIE/SPLIT/NOBOND flipped draft → active in `load_8888.py` + reseeded to prod**;
  deployed 1040 FA export verified = 404 active (401 prior + 3); tts mirror refreshed
  export-verbatim (403 = 404 − the s71-staged FA-1040-4835-06); tts runners
  `_run_8888_assertion` live in BOTH dispatch chains; tts flow gate 503 → 506.
- WORK_ORDERS WO-29 → ✅ DONE. Remaining dispatched set: V/ES → 4868 → 8915-F.

## 2026-07-14 — WO-28 (9465) DONE — tts s85 build leg landed; the three FAs ACTIVATED
- The tts unit shipped (model + compute_9465 pinned to the 10 spec oracles + 17 D_9465_*
  diagnostics + f9465 AcroForm print (packet FRONT tier) + the IRS9465 MeF document with the
  full R-9465-EFILE refusal set + the Payments-tab card).
- **FA-9465-MIN/EFILE/EFW flipped draft → active in `load_9465.py` + reseeded to prod**;
  deployed 1040 FA export verified = 401 active (397 prior + 3 + the known s71-staged
  FA-1040-4835-06); tts mirror refreshed export-verbatim (400 = 401 − the staged id);
  tts runners `_run_9465_assertion` live in BOTH dispatch chains; tts flow gate 500 → 503.
- WORK_ORDERS WO-28 → ✅ DONE. Remaining dispatched set: 8888 → V/ES → 4868 → 8915-F.

## 2026-07-14 — ⟨GATE-1⟩ ×5 APPROVED + SEEDED (tts s83) — WO-28/29/30/31/32 cleared in one approve-all
- **Ken approve-all in-session** (recommendations adopted as filed). Sentinels flipped + approval
  recorded in the five loader docstrings; the five harnesses re-cut to the post-approval guard
  pattern (the 2553/2848 precedent: sentinel-True check + monkeypatch-off refusal proof) and
  re-run — **85/0 (9465) · 53/0 (8888) · 63/0 (1040V/ES) · 97/0 (4868) · 87/0 (8915-F)**.
- **Prod-seeded, SIX TaxForms**: 9465 (46 lines/9 rules/17 diag/10 tests) · 8888 (16/6/12/8) ·
  1040V (6/3/5/3) + 1040ES (8/4/10/7) · 4868 (17/11/16/10) · 8915F (44/10/15/10); 15 FAs staged
  DRAFT. Deployed exports `lookup/{9465,8888,1040V,1040ES,4868,8915F}/export/` = **200 ×6**.
- **FA export verified clean**: the deployed 1040 export = 398 = the tts 397-mirror + the known
  s71-staged FA-1040-4835-06; **zero cluster drafts leaked**. tts mirrors cached
  (`server/specs/{9465,8888,1040v,1040es,4868,8915f}_spec.json`); tts flow gate 500 green.
- → **DISPATCHED: the six tts legs as a set** (9465 · 8888 · V/ES vouchers · 4868 print +
  extension submission builder · 8915-F full unit). Ken-sequenced: the tts SEC-1 authz audit
  runs first (Principle #0), the six legs follow.

## 2026-07-14 — FORM 8915-F draft-to-gate (tts s79) — WO-32 ⏳ AWAITING KEN; NOT seeded
- **The s67 recipe, fifth consecutive gated order**: gap 404 ×2 → verbatim research (f8915f +
  i8915f BOTH **Rev. December 2025** — ⚠ the About page's developments all target older revisions;
  IRS8915F.xsd 2025v5.3 read in full — ReturnData1040, **maxOccurs=6**, per-document name/SSN;
  the 1040 rules CSV = exactly 3 Active F8915F rules) → `f8915f_source_brief.md` → gated
  `load_8915f.py` (28/10/44/15/10 + 3 draft FAs) → `scratchpad/validate_8915f.py` **87/0**.
- ⚠⚠ **The 179-vs-180 one-day asymmetry**: Part I distributions get 179 days after the latest of
  begin/declaration/12-29-2022; Part IV repayments get 180. The IRS's OWN Appendix D (Rev. Jan
  2024) once got this wrong by one day (the 20-Dec-2024 Recent Development) — the period helpers
  pin all EIGHT published date examples in both directions (DR-4682-WA · DR-4681 · DR-4685-GA ·
  DR-4644-VA incl. the SECURE-2.0 floor arm).
- ⚠⚠ **Rev-12-2025 face redesign: NEW line 5a** (non-QDD carve-out; old line 5 → 5b) — the
  2025v5.3 XSD already models it; older-revision guidance mis-numbers.
- **The designation rule** (practitioner surprise): 3-part test holds → ANY distribution incl.
  RMDs/periodic payments/loan offsets is designatable as a QDD, need-blind. $22,000/disaster
  ALL-plans ACROSS-years (F8915F-003 caps 1d); $100,000 only item-B-2020.
- The 11↔22 opt-out boxes MUST match (face verbatim); ÷3.0 rounding convention FLAGGED (the
  9465 ÷72 class); repayments 3y+1d w/ the Rudy forward/carryback examples pinned; the 8606
  15b/25b ties = the tts s75 8606 seam; **line 6 never generates a 5329** (suppression seam);
  landings 15 → 1040 5b, 26 → 4b; worksheets 2-5 attach (BinaryAttachment refs 12/14/23/25);
  Worksheet internals + Appendix A/C/D = stated boundaries (engine-derived).
- ⏭ **Ken now holds FIVE walks (WO-28/29/30/31/32)** — approve-all clears the lane; the six tts
  legs dispatch as a set. Next NEW autonomous item: W-2G → 8879/8878; A2A preempts on WSDLs.

## 2026-07-14 — FORM 4868 draft-to-gate (tts s78) — WO-31 ⏳ AWAITING KEN; NOT seeded
- **The s67 recipe, fourth consecutive gated order**: gap 404 confirmed → verbatim research
  (f4868.pdf 2025 fresh-downloaded + pymupdf-extracted — a self-contained form+instructions doc,
  no separate i4868; About page "None at this time" 30-Mar-2026; the MeF **4868_2026v1.0** package
  found ALREADY LOCAL in tts `docs/mef/schemas/2026v1.0/` — XSDs + the 7-page rules PDF read
  directly) → `f4868_source_brief.md` → gated `load_4868.py` (18/11/17/16/10 + 3 draft FAs) →
  `scratchpad/validate_4868.py` **97/0** → WO-31 staged with the W1-W4 walk.
- **Structural headline: the 4868 is its OWN MeF submission family** (ReturnTypeCd "4868";
  Extensions-family XSDs) — the tts leg is a NEW submission builder, not a 1040 document slot.
  ReturnData = six-element IRS4868 + the s76 IRSPayment (≤1) / IRSESPayment (≤4) records +
  R0000-195 refuses binary attachments (despite the XSD slot).
- ⚠⚠ **The signature story**: a no-payment e-filed 4868 needs NO signature at all (all header
  signature groups optional; the paper face has no signature line). R0000-098 triggers the
  PIN + jurat ladder ONLY when a payment record rides; jurat enum = exactly two values
  (F4868-007/8/9). **FPYMT-052-02 = the EFW tie** (PaymentAmt == L7).
- ⚠⚠ **Two seams FLAGGED for the walk, not resolved**: (1) the TY2026v1.0 FPYMT-088-11 ES-date
  list still prints the 2026 calendar (self-contradictory with FPYMT-086 for a 2027-filed
  extension — stale early-drop carryover; year-keyed); (2) the 2025-face/TY2026-package version
  seam (the TY2026 face publishes ~Oct 2026; re-verify — the s48 face-drift class).
- **The Charlotte trap is now FOUR-way**: GA 4868-with-payment → Box **1302** (V 1214 · ES 1300 ·
  foreign 1303); rosters encoded, 51-jurisdiction partition pinned in the harness.
- Also pinned: L6 "-0-" floor; the L5 Sch-3-L10 exclusion (double-count guard); the 90%-exactly
  safe-harbor boundary; the $525 year-keyed minimum; line-9 Dec-15 landing (DERIVED, walk note);
  the joint-ampersand rule both directions; the 709 filing rider (the 4868↔709 mission seam).
- ⏭ **Ken now holds FOUR walks (WO-28/29/30/31)** — approve-all clears them together; tts legs
  dispatch as a set. Next NEW autonomous item: 8915-F → W-2G → 8879/8878; A2A preempts on WSDLs.

## 2026-07-13/14 — PAYMENT-CLUSTER draft-to-gate BATCH ×3 (tts s77) — WO-28 9465 · WO-29 8888 · WO-30 1040-V/ES pair, ALL ⏳ AWAITING KEN; NOTHING seeded
- **The s67 recipe run three times in one session** (the tts REVIEW_QUEUE s76 batch plan):
  gap 404 ×4 re-confirmed → verbatim research (PDFs pymupdf-extracted; About pages checked;
  the local TY2025v5.3 business-rules CSV + XSDs parsed for the two MeF-channel forms) →
  source briefs (`f9465_source_brief.md` / `f8888_source_brief.md` / `f1040v_es_source_brief.md`)
  → gated loaders (READY_TO_SEED=False ×3) → SQLite harnesses **85/0 · 53/0 · 63/0** →
  WO-28/29/30 staged with W1-W4 walks. `seed_all` discovers the new loaders dynamically and
  soft-fails them by name while gated (verified by reading the orchestrator — no wiring).
- **9465 (WO-28)**: HAS a MeF channel (IRS9465 in ReturnData1040 — InstallmentAgreement family);
  the e-file gate = the published Active F9465-* set, incl. **F9465-019-02 = the tts s76 EFW tie**
  (line 8 == IRSPayment PaymentAmt). ⚠⚠ **Fee-currency catch (the s67 stale-fee class): T.D. 10045
  (91 FR 20902, Apr-2026) amended 26 CFR 300 AFTER the printed i9465 table** — cross-checked the
  LIVE IRS payment-plans page (reviewed 28-Jun-2026): IA fees UNCHANGED, the July-2024 table
  stands ($22/$69/$107/$178; low-income DDIA-waived/$43; modify $89/$43/$10-OPA). Cornell's
  §300.1 is 2016-era — never cite it. Line-10 "÷ 72.0" prints NO rounding → whole-dollar CEILING
  convention, flagged in the walk.
- **8888 (WO-29)**: ⚠⚠ **the Rev. 12-2025 continuous-use face RETIRED the savings-bond program**
  (line 4 "Reserved for future use"; the 2025v5.3 XSD DROPPED the bond group; every bond rule
  Disabled; F8888-023 Active forbids RefundByCheckAmt) — the form is now ONLY the 2-3-account
  splitter; encoded as a refusal so no tts surface resurrects Part II. Both printed $300
  adjustment examples pinned (decrease strips 3→2→1; increase → the last account; BFS offsets →
  LOWEST routing number first — a different ordering, easy to conflate).
- **1040-V/ES pair (WO-30, one order/loader, two TaxForms 1040V+1040ES)**: print-only complements
  of the s76 EFW unit with SUPPRESSION ties (EFW → no V; debited quarter → no paper voucher).
  ⚠⚠ **THREE-WAY address trap: GA mails the V to Charlotte Box 1214 but ES vouchers to Box 1300,
  and the package forbids the Form-1040-instructions address** — both rosters encoded, year-
  watched. ES dates = the FPYMT-088-11 calendar; RAP arms 90/100/110/66⅔ (farmers never 110%;
  $150,000-exactly boundary pinned); the ES WORKSHEET math stays the tts engine's (boundary).
- ⏭ **Ken holds THREE walks — one approve-all clears the whole payment-cluster RS lane**; then:
  flip sentinels → seed prod → verify exports → cache tts mirrors → dispatch the four tts legs
  as a set. Next autonomous tts item while gated: 4868 (spec-first gap check).
## 2026-07-12 — Form 3115 FA activation (tts s70 print unit — Gate-2 shipped; WO-23 fully closed)
- FLOW_ASSERTIONS in `load_3115.py` flipped draft→active (FA-3115-CATCHUP/
  SPREAD/SCHA); prod reseeded (idempotent, status-only; verified active
  in-DB). tts runners (_run_3115_assertion in BOTH dispatch chains) + all
  three gate mirrors refreshed from the deployed export same-session —
  tts flow gate 475 → 484. The tts 3115 print unit is COMPLETE (S-20d);
  **the S-20 admin-forms block (8283-entity/2553/2848/3115) is fully done.**
- ⚠ Citation nit filed (tts REVIEW_QUEUE s70): the spec's IRS_F3115
  citation strings say OMB 1545-0152; the Rev. 12-2022 face prints OMB
  1545-2070 (Cat. No. 19280E matches). Cosmetic — fold into the next 3115
  amendment.
- ⚠ Tooling: PS5.1 `Set-Content -Encoding UTF8` added a BOM to the loader
  during the status flip (stripped). Use python byte-rewrites / Git-Bash
  sed for loader edits.

## 2026-07-12 — GATE-1 ×2 APPROVED + SEEDED: 2553 (WO-26) + 2848 (WO-27) — the S-20b/c RS lane CLEARS (tts s68, live Ken walk)
- Ken asked for the Gate-1 questions "more clearly" → the walks were re-presented
  in plain English (what each spec makes the app DO for a preparer, not spec
  jargon) and put through AskUserQuestion → **"Approve" on both**. The
  plain-English re-present is the better Gate-1 format for autonomous-drafted
  specs — record it as the house pattern.
- Both sentinels flipped (approval + date + scope recorded in the docstrings);
  harnesses re-run post-flip (2553 **82/0** · 2848 **73/0** — the guard-refusal
  pin now proves the mechanism by flipping OFF in-memory); **both seeded to RS
  prod** (2553: 18 authority links — IRC_1361/1362 bound on prod, unlike the
  SQLite harness; 2848: 16 links); **deployed exports verified 200**
  (2553 68,235 B / 2848 60,684 B); **tts mirrors cached from the deployed
  endpoint** (`server/specs/2553_spec.json` / `2848_spec.json` — the s64
  never-hand-splice rule); the FA export verified clean (the 6 new FAs are
  DRAFT and excluded — 1120S still serves exactly 32).
- **→ DISPATCHED to the tts lane: the 2553 + 2848 print units as a pair**
  (render legs + diagnostics code-registration + FA runners/activate/mirror-
  refresh in one motion, the s66 proven recipe). RS TaxForms now 122.

## 2026-07-12 — Form 2848 greenfield DRAFTED to Gate-1 (WO-27, tts Spine S-20c RS leg, tts s68) — ⏳ AWAITING KEN; NOT seeded
- **Second run of the s67 draft-to-gate recipe** (gap 404 → verbatim research →
  `f2848_source_brief.md` → gated `load_2848.py` (READY_TO_SEED=False) → harness
  **73/0** → WO-27 `⏳ AWAITING KEN`). 34 facts / 9 rules / 30 lines / 17 diag /
  9 scenarios / 3 FAs staged DRAFT; entity_types all six suite types; print-first
  (no MeF). The app value-add specced: **L2 preparer autofill from the Preparer
  record** (FA-2848-CAFFILL pins the CAF 9-digit-or-'None' shape).
- **⚠⚠ Research catch — a Recent Development posted FOUR DAYS before the draft
  (08-Jul-2026)**: 5a entries beyond disclosure/substitution/return-signing OR
  any 5b limitation record the POA as **"MODIFIED" on the CAF → the rep loses
  Transcript Delivery System access and Tax Pro Account installment agreements**;
  and "never check line 4 unless Form 2848 is, in fact, a specific-use form."
  Encoded as D_2848_MODCAF / D_2848_L4CAF (warnings with the verbatim substance
  + date pinned in the harness). The About-page Recent-Developments sweep is now
  PROVEN load-bearing — a 2021-revision form carried 2026 guidance.
- Rules: R-2848-MATTER (L3 validity; "All years" → the IRS RETURNS the POA) ·
  R-2848-FUTURE (the CAF future-period clock = Dec 31 receipt-year + 3) ·
  R-2848-SIGNSEQ (**taxpayer-first gives the rep 45 days / 60 abroad; rep-first
  = no limit**; handwritten for mail/fax, e-sign online-only) · R-2848-REPS
  (4 blocks / 2 notice copies / CAF-PTIN) · R-2848-URP (the h-designation
  four-condition gate: PTIN + prepared-signed + AFSP BOTH years; 8821 fallback) ·
  R-2848-AUTH (5a acts + §1.6012-1(a)(5) sign-a-return + modified-CAF) ·
  R-2848-REVOKE (L6 attach-to-retain; REVOKE/WITHDRAW margins; never revokes an
  8821) · R-2848-SCOPE (8821/Form 56 boundaries; one 2848 PER taxpayer) ·
  R-2848-FILE (Memphis/Ogden/Philadelphia chart, year-watched).
- ⚠ topic_name > 255 hit AGAIN (fourth time: WO-22/23/26/27) — trim the topic
  description to a clause list; consider a loader-side truncation guard on the
  next RS maintenance pass.
- ⏭ Ken now holds TWO Gate-1 walks (WO-26 2553 + WO-27 2848) — one "approve
  both" clears the whole S-20b/c RS lane; the tts print units can then build as
  a pair. Next autonomous item: **S-20d 3115 tts app build** (WO-23 DONE, no
  gate).

## 2026-07-12 — Form 2553 greenfield DRAFTED to Gate-1 (WO-26, tts Spine S-20b RS leg, tts s67) — ⏳ AWAITING KEN; NOT seeded
- **The first post-S-16 greenfield order, and the first one drafted-to-gate under
  autonomous mode**: the two human gates are non-negotiable, so the draft stops AT
  Gate-1 — `load_2553.py` ships `READY_TO_SEED = False`, the guard refuses to seed
  (proven in the harness), nothing is on prod, and the tts app build is NOT
  dispatched. Ken's Gate-1 walk (W1-W4) is written into the WO-26 entry +
  tts REVIEW_QUEUE s67 with approve-all recommendations.
- **Research (f2553_source_brief.md)**: verbatim vs Form 2553 Rev. 12-2017 (current;
  no annual reissue) + i2553 Rev. 12-2020 + live where-to-file page (KC/Ogden
  addresses + faxes verified current, page reviewed 2026-03-30). **Catch: the
  printed Q1 user fee $6,200 is superseded → $5,750** per Rev. Proc. 2026-1 App. A
  (A)(3)(a)(ii) — pulled the IRB 2026-1 PDF and quoted it (the first web-summary
  hit cited a stale 2005 fee PDF — the re-fetch-and-quote rule earned its keep
  again). §1362(b)(5) PLR = $14,500; Rev. Proc. 2022-19 §3.03 = the no-PLR path
  for consent/signature defects (via Rev. Proc. 2026-1 §6.03(49)).
- **Draft content**: 28 facts / 8 rules (R-2553-ELIG the eight Who May Elect tests ·
  R-2553-COUNT spouse/§1361(c)(1)(B)-family aggregation + item G · **R-2553-WINDOW
  the 2mo15d corresponding-day deadline calculator — the three published i2553
  examples are pinned scenarios (Jan 7→Mar 21 · Jan 1→Mar 15 · Nov 8→Jan 22) plus
  the no-corresponding-day (Dec 31→Mar 15) and leap-Feb edges** · R-2553-LATE the
  Rev. Proc. 2013-30 path chooser (corporate 1-5 / the 6a-c alternative that lifts
  the 3yr75d cap / entity path + Part IV / PLR) · R-2553-CONSENT timing + signers
  (community-property BOTH spouses; ESBT trustee+deemed owner; QSST deemed owner) ·
  R-2553-PART2 F(2)/(4)→O+(P|Q|R) w/ the P1 47-month receipts gate · R-2553-QSST
  transfer-date gate · R-2553-REELECT the §1.1362-5 five-year bar) / 45 face lines /
  19 diagnostics / 10 scenarios / **3 FAs staged DRAFT** (the new-FAs-default-ACTIVE
  trap; the tts leg will activate + write runners + refresh mirrors in one motion).
  entity_types ['1120S']; print-first (Form 2553 has NO MeF channel — paper/fax).
- Harness `scratchpad/validate_2553.py`: **82 pass / 0 fail** (guard-refusal pin ·
  twice-run idempotent · caps (caught the recurring topic_name>255 trap, trimmed) ·
  deadline/timeliness/count/relief/consent/Part-II oracles · scenario
  expected_outputs recomputed from the helpers · FA draft-status pins · the
  year-keyed fee correction pinned in the D_2553_Q1FEE message).
- `seed_all` impact checked: the gated loader fails soft (per-loader try/except,
  named [FAIL] with the Gate-1 refusal text) — prod rebuilds unaffected.
- ⏭ Next RS order per the SPINE: **Form 2848 (S-20c)** — same draft-to-gate recipe
  (gap-confirmed 404 this session); 3115 (S-20d) needs no RS work (WO-23 DONE).

## 2026-07-12 — 8283 ENTITY ARM amendment (tts Spine S-20a RS leg, tts s65) — the D_8283_010 "not modeled" boundary closes on the entity side
- **Additive amendment to the shared 8283 spec** (load_1040_form_8283.py amends by
  lookup, entity_types preserved 1120S/1065/1040): rules 5→9, diagnostics 13→16,
  scenarios 13→16 (T14-T16), FAs 5→7. Sources: i8283 (Rev. December 2025) PTE +
  Members paragraphs fetched 2026-07-12 and excerpted VERBATIM on
  IRS_2025_8283_INSTR; §170(f)(11)(G) was already excerpted 2026-07-03.
- **New rules**: R-8283-ENTFILE (PTE noncash > $500 files Section A or B WITH the
  1065/1120-S; 1120-S e-file: IRS8283 is a declared ReturnData1120S document —
  2025v6.2 verified; 1065 e-file rides the future 1065 mapper) · **R-8283-ENTSECB
  (the $5,000 Section-B test reads the ENTITY item/group amount — NEVER the
  per-member allocation; i8283 verbatim "even if the amount allocated to each
  member ... is $5,000 or less")** · R-8283-ENTFEED (1120-S: rows total → K12b
  YELLOW default, typed K12b = GREEN override, the tts B11/K16e override-respecting
  pre-pass recipe; **1065: NO FEED — the 2025 face line 13a is a single combined
  cash+noncash Contributions line; print+diagnose only**) · R-8283-ENTCOPY
  (completed copy to each allocated member; v1 = D_8283_015 info + K-1 package
  note).
- **Diagnostics**: D_8283_010 re-scoped IN PLACE to the member-side attach
  choreography (the entity side is now modeled); NEW D_8283_014 error (entity
  noncash > $500 with no rows — replaces the tts s63 D_SCHK_8283 "form not built"
  warning) · D_8283_015 info (copy to members) · D_8283_016 warning (1065: 13a
  must cover the noncash total).
- **FAs staged DRAFT** (FA-ENT-8283-01/02) — the new-FAs-default-ACTIVE trap:
  the tts s64 export-verbatim gate mirrors must not pick them up before their
  runners land (the tts S-20a tts leg activates them + refreshes the mirrors
  together).
- Judgment items J-E1 (1120-S K12b feeder) / J-E2 (1065 no-feed) / J-E3
  (copy-to-members info-first) queued in tts REVIEW_QUEUE s65 with
  recommendations — the s59 shipped-plus-ratification-queued pattern.
- Harness scratchpad/validate_8283_entity.py: 45 checks green (twice-run
  idempotent; pre-polluted old D_8283_010 title overwritten; T14/T15/T16
  arithmetic oracles; draft-status pins; verbatim-phrase pins). Prod seeded
  (9 rules / 16 diags / 16 scenarios / 7 FAs, all rules cited); deployed
  export verified (the 1120S FA export still serves exactly 30 — drafts
  excluded); tts mirror server/specs/8283_spec.json refreshed; tts flow gate
  460 + test_compute_8283 green against the refreshed mirror.

## 2026-07-12 — 1120S_M3 line_map renumbered to the REAL face (audit unit #7) — the queue's last standalone item; the $50M tier un-conflated (tts s62)
- **The face finally entered the repo**: f1120ss3.pdf (Rev. December 2019 — the CURRENT
  revision; its instructions i1120ss3 are also Rev. 12-2019), fetched + pymupdf-extracted
  2026-07-12 and registered in the tts manifest (84). **⚠ irs.gov filename trap: the
  obvious guess `f1120sm3.pdf` is the Form 1120 (C-corp) M-3 — in that name "s" means
  "schedule"; the 1120-S schedule is `f1120ss3.pdf`** (found via the IRS search index).
- The old block's P1-*/P2-*/P3-* line_map — flagged "unverifiable, no face in repo" by
  the s44 audit — proved FABRICATED: Part III ends at line 32 (the spec ran P3-33..36,
  shifting "other items with no differences"/"reconciliation totals" onto phantom rows);
  Part I "line 1" was labeled net income (the real line 1 is the 1a/1b income-statement
  questions; net income per statement is line 11 = COMBINE 4-10); and P1-FS/P1-RS/
  P2-DEP/P3-DEP exist on no revision.
- Rebuilt verbatim (`_load_m3` in load_1120s_complete): 30 face-keyed facts (1a/1b
  booleans · line-2 period dates · 3a/3b restatements · 4a + the 4b GAAP/IFRS/tax-basis/
  other choice · 5a-10 reconciliation amounts w/ the parenthesized-subtraction notes ·
  the 12a-d entity asset/liability grid · the filing gates) · **R001-R005** (R001 $10M
  filing gate — reads SCHEDULE L EOY assets, i1120ss3 Who Must File verbatim; R002 P1
  L11 combine; R003 Part II columns + L23/L26 + the tie notes; R004 P3 L32 = combine
  1-31 carried to P2 L24 SIGN-FLIPPED, face verbatim; **NEW R005 = the completion
  tiers: >= $50M must complete ENTIRELY; required-under-$50M or voluntary filers may
  complete through Part I + Schedule M-1 with M-1 L1 == P1 L11 — this $50M tier is
  what the pre-s44 spec had conflated into a $50M FILING threshold**) · 87 face lines
  (I-1a..I-12d · II-1..26 incl. 21a-g · III-1..32 incl. 23a/23b + the Reserved 22) ·
  D001-D007 (NEW: the $50M-entirely error arm, the L26(a)/L26(d)/M-1-L1 tie errors,
  the item-C checkbox warning) · 5 scenarios (kept 2 threshold pins now tier-aware +
  NEW published Example 1 "$12M consolidated FS / $8M Schedule L = NOT required" +
  the P1 L11 combine oracle + the P3 L32 sign-flip/L26(d)=K18 oracle).
- **Tie chain now specced end-to-end**: P1 L11 = P2 L26(a) (or Schedule M-1 line 1
  under the through-Part-I option); **P2 L26(d) = Form 1120-S Schedule K line 18** —
  the same K18 anchor the s56/s59 units established for M-1 L8. Excerpts: 5 verbatim
  (Who Must File · the Completing tiers — **transcribed verbatim incl. the IRS's own
  "(Form 1065)" typo, flagged in a NOTE and not propagated into rules** · the
  Purpose/tie notes · the L32 sign-flip · the item-C checkbox); the old excerpt's
  "UNVERIFIED against the face" warning retired; source citation → (Rev. December 2019).
- Link hygiene: RuleAuthorityLink refresh-deletes on BOTH the M-3 block and the SCHB
  block — **the s44 $10M threshold fix had left SCHB R003's link note still reading
  "M-3 threshold: $50M total assets" in prod** (get_or_create never updates notes);
  healed and verified in the deployed SCHB export.
- Validation: `scratchpad/validate_m3_renumber.py` **165/0** on throwaway SQLite —
  twice-run pre-polluted (incl. a re-created stale SCHB note shape), scenario oracles,
  link coverage, excerpt labels, caps. Prod seeded — stale-deletes exact (13 fabricated
  facts + all 20 fabricated line rows); idempotent rerun clean; deployed
  lookup/1120S_M3/export/ verified (87 lines / R001-R005 / 30 facts / D001-D007 / 5
  tests); NEW tts mirror `server/specs/1120s_m3_spec.json`.
- tts drift check: **boundary-RED by design** — no M-3 render/compute/MeF leg exists
  season one; the three $10M threshold constants (rules_entity_boundary/rules_8825/
  rules_1065_l) verified correct and reading Schedule L 15d; the "prepare manually"
  routing unaffected by the through-Part-I nuance.
- **The s44 renumber queue is CLEARED**: 4562 ✅s45 · SCH_K ✅s56 · K1 ✅s57 · SCHL ✅s58 ·
  PAGE1+M1+M2 ✅s59/s60 · 6198 ✅s61 · M3 line_map ✅s62 — remaining: **3800**, deferred
  by design to the future 3800/GBC entity unit (the largest rebuild; pre-2023 layout).

## 2026-07-12 — Form 6198 renumbered to the REAL face (audit unit #6) — a NEW Rev. 11-2025 revision; tts leg-less, no drift possible (tts s61)
- **6198 rebuilt verbatim** (load_1120s_complete `_load_6198`) vs f6198.pdf **Rev.
  November 2025** — a NEW revision (Created 9/9/25; the local template hash-matches a
  fresh irs.gov download) — + i6198 (Rev. November 2025, fetched + pymupdf-extracted
  2026-07-12). The old block was the audit's FABRICATED-line_map verdict: an invented
  "prior year unallowed losses" line 2 (the face folds prior-year nondeductible amounts
  INTO the Part I lines-1-4 entries — now rule R009), deductible loss on 20 (face: 21;
  20 = amount at risk, larger of 10b/19b), and 13 of 21 face lines missing.
- Now: 21 face-keyed facts (incl. line15_basis/since_when_16/since_when_18 choice facts
  for the three a/b checkbox pairs; qualified_nonrecourse_financing KEPT as the L7/L16
  component breakdown driving D002) · **R001-R009 — the §465 substance kept, re-keyed**
  (R001 Part I combine 1-4 · R002 Part II 6-10b · R003 Part III 11-19b incl. the 15b
  prior-year-19b-NEVER-10b caution · R004 L20 larger-of · R005 L21 smaller-of + the
  multi-item pro-rata carryover · R006 QNF §465(b)(6)/Reg. 1.465-27 · R007 §465(e)
  recapture incl. the profit-year caution · R008 basis→at-risk→passive ordering, ties
  the FORM_8582 spec's R-8582-ATRISK-ORDER · R009 prior-year nondeductible) · 25 face
  lines · D001-D006 · 7 scenarios: the THREE published i6198 Line 21 examples, the p.3
  Line 5 income-offset example (-4,600 + 3,100 → allowed 3,700), Part II, Part III +
  larger-of, and the kept QNF-substance pin.
- **Fabricated-excerpt class (again):** IRS_2025_6198_INSTR's sole "At-risk computation"
  excerpt was a paraphrase. Replaced VERBATIM under the SAME label (rename-orphan guard)
  + 5 new verbatim excerpts; citation → "(Rev. November 2025)"; `forms_supporting.py`
  mirrors the set so a load_all_federal rerun agrees (sibling-drift guard). In-loader
  RuleAuthorityLink refresh-delete (the s59 stale-note rule) + fact/line/rule/diag/
  scenario self-heal whitelists (6198 is single-owner — exact).
- Validation: `scratchpad/validate_6198_renumber.py` **144/0** on throwaway SQLite —
  twice-run against a pre-polluted DB (self-heal proof), arithmetic oracles for all 7
  scenarios, link coverage, excerpt labels, CharField caps. Prod seeded — stale-deletes
  fired exactly (9 facts / lines 2+10 / 2 scenarios); idempotent rerun clean; deployed
  `lookup/6198/export/` verified (25 lines / R001-R009 / 21 facts / D001-D006 / 7
  tests); tts mirror NEW `server/specs/form_6198_spec.json`.
- **tts drift check: NO 6198 leg exists** — field map is an unmapped stub (not in the
  renderer registry), zero MeF/seed refs; compute references are ordering comments +
  compute_4835's at-risk cap (min(|loss|, at_risk_amount)) which matches R005. The
  fabricated map never leaked into the app. Housekeeping: f6198.pdf was an UNREGISTERED
  template — registered in tts forms_manifest.json (83; trip-wire bumped).
- Renumber queue remaining: **M3 line_map (unit #7 — M-3 face template download first)
  → 3800 (rides the GBC entity unit)**.
- *(Log continuity note: the s59 PAGE1/M1/M2 RS leg (RS `bb42381`, load_1120s_full) and
  the s60 tts FFV re-key were run from the tax-app context and are documented in
  BUILD_ORDER.md (tts-tax-status) + tts STATUS_ARCHIVE/form_coverage_tracker — this
  log skipped from s58 to here.)*

## 2026-07-11 — 1120S_SCHL renumbered to the 2025 face (audit unit #4) — tts verified face-correct, RS-only drift (tts s58)
- **1120S_SCHL rebuilt verbatim** (`bfcb95a`) vs f1120s.pdf (2025) p.4 + i1120s p.49. The
  old block ran TWO fabricated numbering systems at once: facts had total assets at l14 /
  liabilities 15-21 / l6 "other investments" / l7 "buildings" (face: 6 = other current
  assets, 7 = loans to shareholders), while the line map invented an "L22 Total
  liabilities" (no such face line) shifting equity +1 into a phantom L28. Now: 65 facts
  (31 face rows × BOY/EOY + 3 cross-checks) · 8 rules (R001 total-assets sum gains lines
  4/6/7/8 + the 2/10/11/13 contra pairs; **fabricated R002 total-liabilities rule
  DELETED — first use of a stale-RULE self-heal**; R004 = L15==L27; R007 tied to the
  Sch B Q11 gate verbatim; **NEW R009 = L15 col (d) → page 1 item F**, p.49 verbatim;
  R005/R006/R008 substance kept per the audit) · 31 face lines · 7 diagnostics (NEW D007
  item-F mismatch) · 4 scenarios (NEW contra-pair netting pin).
- **⚠ Fabricated-excerpt class:** the block's two AuthorityExcerpt rows were paraphrases
  carrying the same wrong numbering — the drift had manufactured its own "authority."
  Replaced with real p.49 verbatim text, KEEPING the excerpt labels (update_or_create
  keys on label; a label change would orphan the old row — the rename-orphan class).
  Audit rule going forward: verify a block's excerpts against the PDF too.
- Prod stale-deletes fired exactly: 26 orphan facts + R002 + lines L11/L28. SQLite
  validate first; idempotent rerun clean; deployed export verified; tts mirror refreshed.
- **tts verified FACE-CORRECT end-to-end** (seeds L1a-L27d · compute L15/L27 sums match
  R001/R003 exactly · L24d←M-2 · $250K check reads L15d · MeF SCHL_LINE_ORDER incl.
  derived contra nets · item F ← L15d in both print and MeF) — no app change; the zone
  y-band-pinned (tts TestScheduleLRowPins).
- Renumber queue remaining: **PAGE1+M1+M2 (unit #5** — pre-7205 numbering + the
  fabricated M-1 excerpt; the tts FFV re-key + data migration + the seven s56 deferrals
  ride it**)** → 6198 → M3 line_map → 3800.

## 2026-07-11 — K1_1120S renumbered to the 2025 face (audit unit #3) — the tts "codes mirror the tables" belief FALSIFIED (tts s57)
- **K1_1120S rebuilt verbatim** (`a0e908c`) vs f1120ssk.pdf (2025) + i1120s (2025)
  pp.30-48: full boxes 1-19 line map (14 = Schedule K-3 checkbox, 15 = AMT codes A-F,
  18/19 = multi-activity checkboxes), Part I item D + Part II items E-I (F2 responsible
  party / F3 entity type / item I loans), and the REAL 2025 code tables — the old block's
  box 12/13 "code letter" claims mirrored the Schedule K sub-line letters (the pre-2023
  alphabet). NEW rules R012 (box 12: cash A/B · noncash C-G · investment interest H ·
  §59(e)(2) J · other ZZ), R013 (box 13: **13a→C, 13b→D, 13c→E, 13d→F, 13e→G, 13f→I;
  13g own codes A/B/H/J-BC incl. 8941=BA**), R014 (K-3 checkbox), R015 (AMT A-F), R016
  (box 16 A/B/C/F pro rata; D/E per-recipient), R021 (box 17 A/B + the C-BA/ZZ 17d list);
  R017 gains the V*/STMT mechanics; R-K1-ROUND's "box 17 AC health insurance"
  parenthetical corrected. Diagnostics D004 (pre-2023-alphabet error) / D005 (health
  insurance ≠ code AC — i1120s p.17: W-2 box 14 is the channel; AC = §448(c) gross
  receipts) / D006 (charitable code-A 60%-cash assumption). 7 verbatim i1120s excerpts
  on IRS_2025_1120S_INSTR. In-loader fact/line/scenario self-heal guards (the s56
  rename-orphan class, now standard). 4 new code-pin scenarios.
- Seeded (44 facts / 17 rules / 33 lines / 6 diag / 7 scenarios; SQLite validate +
  Supabase, idempotent rerun clean) + export verified (lookup/K1_1120S/export/
  content-checked) + tts mirror refreshed.
- **The audit's verify arm found FOUR live tts print/MeF code zones** (tts `69e7e08`):
  box 13 emitted the pre-2023 letters (LIH printed "A" = zero-emission nuclear on the
  2025 table), K12c §59(e)(2) "I" (= royalty deductions; face J), K12d "L" (= portfolio-
  other; face ZZ), health insurance "AC"; plus K13e never allocated (the MeF builder
  referenced a box_shares key the issuer never produced). All re-lettered print+MeF,
  pinned. Details: tts STATUS/form_coverage_tracker s57.
- Renumber queue remaining: **SCHL (unit #4)** → PAGE1+M1+M2 → 6198 → M3 line_map → 3800.

## 2026-07-11 — SCH_K_1120S renumbered to the 2025 face (audit unit #2, WO-25) + RET-G5 orphan fix (tts s56)
- **SCH_K_1120S rebuilt verbatim** vs f1120s.pdf (2025) pp.3-4 + i1120s pp.40/49: the
  fabricated 13f "Foreign tax credit" → **Biofuel producer credit** (foreign taxes = 16f);
  rehab credit 13d → 13c; 12d/12e fixed; added 3a/3b/3c (R009 netting), 8b/8c, 13b/13e,
  14a/b K-2 checkboxes, 15a-f, 16e/16f, the **17a-d split — 17c AE&P dividends are
  1099-DIV-only, never K-1 (i1120s p.40 verbatim, now diagnostic D005)**; L18 = combine
  1-10 − (11-12e) − 16f (R019), ties to **M-1 line 8** per i1120s p.49.
- **Tax-law error corrected in load_1120s_full**: R018 + D012 said "K18 must equal Page 1
  Line 21" — WRONG (separately stated items differ; the tie is M-1 L8 / M-3 II-26(d)).
  R010's "Page 1 Line 21" → 22 (2025 face inserted line 19, Form 7205).
- In-loader stale deletes: line "17" catch-all, fact `foreign_tax_credit`; the line
  allow-set includes load_1120s_full's K*->Box* rows so a base reseed can't stomp them.
- Seeded (52 facts / 19 rules / 47 face lines / 6 diag / 6 scenarios) + export verified
  (lookup/SCH_K_1120S/export/ = 200, content-checked) + tts mirror refreshed.
- **NEW audit finding (queued after SCHL): 1120S_PAGE1 + M1 + M2 blocks in load_1120s_full
  are pre-Form-7205 numbering** (OBI on 21 vs face 22; tax/payments restructured 23/24a-z)
  **+ the M-1 "verbatim" excerpt contains a fabricated line** ("3a guaranteed payments" is
  a 1065 M-1 line; the 1120-S 3a is depreciation). Ledger: tts docs/rs_handoff.
- **RET-G5**: `load_1040_retirement._upsert_tests` now deletes orphaned scenario rows
  (renames leave the old scenario_name row behind — the rename-orphan class); reseeded,
  the stale "unsupported exception 13" row deleted from the DB; re-exported.
- tts-side print fixes from this trip (page-1 row shift, K13/K12 shifts, K17c off the
  K-1) live in the tts repo — see tts STATUS_ARCHIVE s56.

## 2026-07-10 (later again) — 8825 renumbered to the Dec-2025 face + Schedule A (Form 8825) mechanics (tts s48)
- The batch-2 8825 group's spec-first leg. **The Session-10 8825 block was ANOTHER
  early-era drifted spec, found OUTSIDE the s44 audit queue** — its numbering (other 15 /
  total 16 / net 17 / total-net 21) matches NO published revision. Rebuilt verbatim vs
  f8825.pdf + i8825.pdf Rev. 12-2025 (both fetched today) + IRS8825.xsd 2025v6.2.
- New face encoded: 2a/2b/2c income split (2b NEW) · 15/16 reserved · line 17 = the NEW
  **Schedule A (Form 8825)** fixed-category schedule (A1-A20 + A30; i8825 verbatim:
  REQUIRED only for Schedule M-3 filers; A31 total → line 17) · 18 = sum(3-17) · 19 =
  2c − 18 · **23 = COMBINE 20a-22a → K2 (the old R003 "K2 = sum(net_rent)" OMITTED
  21/22a — corrected)** · col (b) 1-8 + NEW col (c) A-I codes (M-3-only Note verbatim).
- 34 facts (structured address; choice lists) · R001-R007 · 58-line map (A1-A31) ·
  D001-D005 · 5 scenarios · 8 re-fetched verbatim excerpts (2 stale 2026-03-18 excerpts
  deleted in-loader) · in-loader stale fact/line DELETE.
- **⚠ Seeding lesson: prod was seeded via a SCOPED script** (scratchpad/
  seed_8825_renumber.py runs only _load_sources + _load_8825) — re-running the whole
  load_remaining_1120s would stomp 4562 R011, which the later
  load_4562_section179_carryover amend loader owns. Full rebuilds stay correct via
  seed_all's base-then-amend ordering.
- SQLite harness 123 checks green (scratchpad/validate_8825_renumber.py, incl. a
  pollute-then-reseed self-heal proof) · Supabase-seeded · deployed export verified ·
  tts mirror refreshed. RS commit `c4c94bc`; the tts build landed same-session
  (`a4435f4`: migs 0184/0185, four live print-bug fixes, f8825sa print, MeF
  GeneralDependencyMedium detail, D_8825_001-005, the B2-7a/8/9 UI).
## 2026-07-10 (later still) — 4562 §168(k)(7) election-out unit (R009) + the R007 AMT-arm tax-law correction
- The s46 stated follow-on, spec-first. i4562 2025 fetched + read verbatim (p.7 Election
  out; p.6 the OBBBA 40%-instead-of-100% transitional election — NO statement mechanics
  stated, spec-silent → tax-app REVIEW_QUEUE, not implemented).
- **⚠⚠ R007 CORRECTED — a tax-law error in yesterday's matrix:** the election-out arm
  claimed the AMT 150DB recompute re-engages on a (k)(7) election. Both 2025 instructions
  say otherwise, verbatim: i6251 line 2l ("It isn't subject to an AMT adjustment for
  depreciation if it was placed in service after 2015") + the i4562 p.7 Note ("will not
  be subject to an AMT adjustment"). Mechanism: (k)(7) switches off only §168(k)(1)/(2)(F),
  so the (2)(G) exemption survives — ELIGIBILITY controls post-PATH, not claiming. Formula
  now keys on NEW fact `bonus_eligible` (150DB only for never-eligible 200DB property);
  scenario 6 re-pinned; flagged for Ken's ratification (reverses one arm of the
  Ken-attributed matrix — REVIEW_QUEUE s47 in the tax app).
- **NEW R009** (conditional): per-class election out — i4562 p.7 verbatim (all property
  in the class, statement on the timely filed return, 301.9100-2 six-month cure,
  irrevocable, per-entity) + the four engine effects (bonus=0 per class · NO AMT
  adjustment · RP 2025-16 §2.03(2) Table 2 for under-6000 autos · GA add-back eliminated
  — the firm's reason for electing out) + the why-the-election-matters note (§168(k)(1)
  "shall" + §1016(a)(2) allowed-or-allowable).
- **Facts:** NEW `bonus_electout_classes` (return-level; tokens 3/5/7/10/15/20/25 +
  software; Reg. §1.168(k)-2(f)(1) finer classes NOT fetched — flagged) + NEW
  `bonus_eligible` (per-asset, default true). amt_method fact notes corrected.
- **Diagnostics:** D008 bonus-inside-an-elected-out-class (error) · D009
  bonus-zeroed-without-the-election (warning).
- **Sources:** IRS_2025_4562_INSTR gains 2 verbatim excerpts (Election out p.7 incl. the
  AMT Note; the p.6 40%/60% transitional election). R007/R009 gain i6251/IRC_168/
  RP 2025-16 links (4 each).
- **Scenarios:** 3 new (elect-out lifecycle: bonus 0 / full-basis MACRS / AMT SAME /
  GA 0 / statement · D008 conflict · elected-out auto Table-2 12,200); scenario 6 + 8
  notes corrected. 4562 loader now 25 facts / 9 rules / 9 diags / 17 scenarios.
- SQLite-validated (db_validate; load_1040_form_6251 run first so the i6251 source links
  resolve — R007/R009 4/4 links) → Supabase-seeded → deployed lookup/4562/export verified
  (R009, D008/D009, both facts, 28 merged scenarios) → tts mirror form_4562_spec.json
  refreshed. RS commit `fdeadfb`.
- tts side (same session): mig 0183 · engine election + AMT fix · statement page + the
  DECLARED ElectNotClaimSpclDeprecAllwnc MeF doc (ReturnData1120S ref 1921) · UI
  checkboxes · engine 63 / flow 447 / MeF 69 / render 25 all green.

## 2026-07-10 (later) — 4562 depreciation-methods unit (Ken's Lacerte method list delivered)
- Ken delivered the method/life/vehicle-classification dropdown list + the AMT method
  matrix → spec-first amendment to the freshly-renumbered 4562 block (load_1120s_specs).
- **Facts:** `depreciation_method` choices → 200DB/150DB/SL/SL_RES/SL_NONRES/ADS_SL/NONE
  (Ken's 7, display labels + the "passenger auto is a CLASSIFICATION, not a method" ruling
  in notes); `recovery_period` choices += 30/31.5/40 (31.5 = legacy nonres PIS >1986 <5/13/1993
  → Table A-7; 30/40 = ADS real → A-13/A-13a); NEW `vehicle_classification`
  (under_6000 / work_truck_6ft / over_6000) + NEW `amt_method` (SAME/150DB, derived).
- **Rules:** R003 description rebuilt = the Chart 1/Chart 2 published-table routing +
  the never-derived-arithmetic mandate + refuse-on-unmapped-combination (D007). NEW R007
  AMT post-1998 matrix (i6251 line 2l quoted 2026-07-10: 150DB same life+convention ONLY
  for 200DB property with NO §168(k) allowance claimed; SL/150DB/ADS/residential/nonres/
  bonus-claimed = SAME; §168(k)(7) election-out re-engages the recompute; pre-1999 §1250
  accelerated = out of scope, flag). NEW R008 vehicle caps by classification (§280F
  under-6000 only — Rev. Proc. 2025-16 T1/T2; §179(b)(5)(A) $31,300 SUV cap over-6000;
  work_truck_6ft = the §179(b)(5)(B)(ii)(II) ≥6-ft-bed exception, no caps).
- **Sources:** IRS_PUB_946 gains 6 verbatim table excerpts (Chart 1 routing · A-14 3/5/7/10
  columns · A-2..A-5 ALL columns · A-15..A-18 3/5/7/10 · A-7 31.5-yr · A-13/A-13a ADS 30/40)
  — pymupdf-extracted from p946.pdf 2026-07-10. NEW sources IRS_RP_2025_16 (2025 auto caps
  T1/T2 verbatim + §2.03 when-Table-2 incl. the (k)(7) election-out) and IRS_RP_2024_40
  (§2.25 SUV $31,300 verbatim). IRC_179 gains the §179(b)(5) excerpt; NEW IRC_280F source.
- **⚠⚠ TWO LIVE tts-ENGINE BUG CLASSES exposed by the verbatim tables** (fix rides the tts
  engine leg, this unit): (1) the entire MACRS_200DB_MQ dict was DERIVED-wrong (published
  A-3 Q2-5yr = 11.37/11.37/4.26 vs engine 11.98/11.98/3.04; the Q4 column summed to 99.00%);
  (2) MACRS_150DB_HY 10-yr had the SL switch a year late (published yr-5 = 8.74, engine 8.53).
  Also the LUXURY_AUTO_LIMITS constants were wrong (19,500 yr-2 / 12,400 no-bonus yr-1 vs
  published 19,600 / 12,200) AND miscited "Rev. Proc. 2025-13" (= the §831(b) micro-captive
  proc, not autos — the real source is Rev. Proc. 2025-16).
- **Diagnostics:** D005 vehicle-without-classification (warn) · D006 SUV §179 > $31,300
  (error) · D007 unmapped method/life/convention = REFUSE, never silent 0% (error).
- **Scenarios:** 9 new published-value pins (AMT trio incl. bonus-claimed-no-adjustment ·
  31.5 month-6 1.720% · ADS 40/30 · MQ Q4-5yr A-5 pin · 150DB yr-5-switch + A-15 Q1 pin ·
  auto cap 20,200 · SUV 31,300 vs work-truck exempt). 4562 now 22 facts / 8 rules /
  60 lines / 7 diags / 14 scenarios in this loader.
- SQLite-validated (scratch db_validate.sqlite3, all 4562 rules linked) → Supabase-seeded
  (TaxForms 121, amendment-only) → deployed lookup/4562/export verified (R007/R008,
  choices, D005-D007, 24 merged scenarios) → tts mirror form_4562_spec.json refreshed.
- Boundary: the §168(k)(7)/(k)(10) ELECTION mechanism itself (per-class election input,
  statement doc, GA add-back kill, 280F Table-2 flip, AMT re-engagement) is the NEXT
  spec unit — R007/R008 already state the interplay verbatim so it drops in.

## 2026-07-10 — 4562 renumbered to the 2025 face (renumber unit #1 from the s44 early-era audit)
- Rebuilt load_1120s_specs._load_form_4562 VERBATIM vs f4562.pdf 2025 (rev "Created
  10/9/25", pymupdf dump) + IRS4562.xsd 2025v6.2 LineNumber annotations. The old block
  carried a fabricated pre-2025 shape: lines 6/7 swapped (face: 6 = the §179 property
  table, 7 = listed property from line 29), line 8 as a "smaller of" (face: ADD column
  (c) lines 6 and 7), line 12 without the line-10 carryover, and the pre-2025 line-19
  lettering. Line map now the FULL face: 26 rows → 60 (Part I 1-13; Part II 14-16;
  Part III 17/18, 19a-19j, 20a-20e; Part IV 21/22/23a/23b; Part V 24a/24b/24c + 25-41;
  Part VI 42-44).
- **THE 2025 FACE CHANGE: 19h "50-year property" is NEW** (50 yrs./MM/S,L), shifting
  residential rental → 19i and nonresidential real → 19j; Section C adds 20e 50-year.
  New structural scenario pins the re-letter (h=50/i=residential/j=nonresidential).
  recovery_period fact gains choice "50". R006 relabeled Part VI (amortization);
  R001/R005 descriptions restated face-verbatim. NEW fact listed_sec179_elected (line 7).
- Lines 10-13 mirrored VERBATIM from load_4562_section179_carryover (Ken-approved
  2026-06-22) so reseed order can never regress them; R010-R015/D010-D014 ids untouched.
  In-loader stale-row DELETE added (SCHD/SCHB recipe) — zero rows deleted on Supabase
  (every pre-2025 number still exists on the face; descriptions updated in place).
- SQLite-validated → Supabase-seeded (TaxForms 121, amendment-only; 4562 = 20 facts /
  6+6 rules / 60 lines / 5+10 scenarios merged across its three loader homes) →
  deployed lookup/4562/export verified (19h/19i/19j/20e/23a/23b/24c present; line 12
  carryover wording intact) → tts mirror form_4562_spec.json refreshed.
- **tts side (same unit): the field map was LIVE-WRONG on the 2025 PDF** — it keyed
  residential rental to the PDF's Line19h row (= the 50-year row) and nonresidential
  to Line19i_1 (= the residential row). Fixed: f4562_derivation.MACRS_LINE_MAP
  re-lettered (27.5→i, 39→j, +50→h), field map re-keyed + NEW L19j_* (Line19j_1),
  MeF _GDS_ELEMENTS re-lettered + GDS50YearPropertyGrp emission (PIS REQUIRED —
  refuse on mixed-month aggregation). MeF XML for residential/nonres is UNCHANGED
  (elements were already semantic). Pins: MACRS_LINE_MAP letters, y-band row
  placement on the filled PDF, GDS lettering/order, 50-yr mixed-month refuse.
- ⚠ Deferral (tts DEFERRAL_AUDIT): _macrs_pct has no 50-year SL/MM table (silently
  returns 0% — pre-existing class; railroad grading/tunnel bores, never seen at the
  firm). Needs its own verified-source unit if ever hit; print/MeF channels are ready.
## 2026-07-09 â€” Early-era FACE AUDIT (retrospective B, Ken-approved) + M-3 threshold TAX-LAW FIX ($50M â†’ $10M)
- Ken approved the tts retrospective proposals; item B = audit every "Session 11"-vintage
  1120-S-family block against the 2025 faces. Full ledger:
  tts `docs/rs_handoff/2026-07-09_early_era_face_audit.md`. Verdicts: SCHD_1120S CLEAN
  (the s34 renumber verified verbatim) Â· 1120S_SCHL DRIFTED-internally-contradictory
  (fabricated "L22 Total liabilities" + a second fabricated numbering in the facts) Â·
  SCH_K_1120S DRIFTED worst (fabricated 13f "FTC" row â€” face: Biofuel producer credit;
  missing 17c AE&P; wrong line-18 formula) Â· K1_1120S DRIFTED (box 12/13 code letters
  wrong vs the 2025 instruction tables) Â· 4562 DRIFTED incl. a MISSED 2025 FACE CHANGE
  (new 19h 50-year property row â†’ residential 19i / nonresidential 19j) Â· 6198 + 3800
  FABRICATED Â· 1120S_M3 face-not-in-repo. Queued renumber order: 4562 â†’ SCH_K â†’ K1 â†’
  SCHL â†’ 6198 â†’ M3-line_map (needs the face template) â†’ 3800.
- **FIXED + SEEDED THIS SESSION: the M-3 filing threshold.** i1120s 2025 p.49 verbatim
  (verified twice in-PDF): "Corporations with total assets of $10 million or more on the
  last day of the tax year must file Schedule M-3 (Form 1120-S) instead of Schedule M-1."
  The spec said $50M everywhere â€” 1120S_M3 R001/D001/D002/notes/fact label + BOTH source
  excerpts (M3_INSTR + the SCHB M-3 excerpt) + SCHB R003 (authored yesterday â€” it had
  propagated the error). New $12M-band scenario pins the band the old threshold mis-gated.
  SQLite-validated â†’ Supabase-seeded â†’ deployed exports verified (M3 R001 `>= 10000000`,
  SCHB R003 same) â†’ tts SCHB mirror refreshed. NOTE: the tts engine was ALREADY correct
  at $10M (`rules_entity_boundary` / `rules_1065_l`) â€” spec-only error.

## 2026-07-09 â€” 1120S_SCHB renumbered to the 2025 face + R006 Q11 auto-answer (Ken ruling; tts s42 item 12)
- Ken ruled (tts s42, usability item 12): Schedule B question 11 is AUTO-ANSWERED â€” derived,
  YELLOW, preparer-overridable; Schedule L/M-1 behavior and diagnostics unchanged. Spec-first.
- FOUND while verifying: the `load_1120s_complete.py` SCHB block carried a FABRICATED pre-face
  numbering (~20 questions; its "B11" = an AE&P question that does not exist on the 2025
  Schedule B; "B3" shareholder count actually lives on page 1 item I). The tts seed already
  followed the 2025 face â€” RS-only drift. Rebuilt the block verbatim vs f1120s.pdf 2025
  (pp.2-3): lines B1-B17 (incl. B12_amount/B15_amount matching the tts/MeF keys), 28 face-keyed
  facts, verbatim excerpt pair (the face question list + the i1120s (2025) p.24 "Question 11"
  total-receipts definition). **Stale rows DELETED in-loader** (the F4797-G2/SCHD recipe): on
  Supabase, 7 line rows + 20 fact rows removed. Practice rules KEPT re-keyed and labeled
  non-face-question (Â§1375 AE&P trigger Â· M-3 $50M Â· shareholder-count cross-check Â·
  100-shareholder limit); diagnostics re-keyed (D002 now b8_nubig_amount > 0; D003 now the
  14a-Yes/14b-No pair).
- NEW **R006** "Question 11 auto-answer (derived, overridable)": b11_under_250k =
  (q11_total_receipts < 250000) AND (l15_total_assets_eoy < 250000); the component sum names
  each source line; positive-only reading of the "income or net gain" components (and p1 4/5)
  flagged as interpretive; the Schedule-L/M-1-unchanged boundary stated in the description
  (1120S_SCHL R007 remains the separate filing-exception statement); TY2026 re-verify note.
  Scenarios: "Q11 auto-answer â€” small corp (Yes)" (180,000/90,000) and "assets at threshold
  (No)" (249,999/250,000 â€” strict less-than).
- SQLite-validated (db_validate.sqlite3) â†’ Supabase-seeded (TaxForms 121 â€” amendment-only) â†’
  deployed `lookup/1120S_SCHB/export/` verified (R006 + 23 lines + 28 facts + 5 scenarios) â†’
  cached to tts as NEW `server/specs/1120s_schb_spec.json`. tts built same session
  (`_auto_answer_b11_db` + amber Auto UI; 5 DB tests; flow 447). RS `b7907bc`.
- Handoffs for Ken (tts REVIEW_QUEUE): ratify the SCHB renumber/practice-rule re-keying Â·
  the 1065 Schedule B Q4 sibling (4-condition test, $1M assets, timely-K-1 conduct condition)
  needs its own ruling before authoring Â· K3a-gross capture question (tts nets K3).

## 2026-07-09 â€” M&E four-tier worksheet: 1120S_PAGE1 R009/R010 + 1065_PAGE1 R-1065P1-MEALS/-MEALSND (Ken ruling)
- Ken ruled (tts s41, usability item 9): add the NEW 100% fully-deductible-meals line to the
  M&E worksheet â€” spec-first. Encoded the four-tier worksheet (100/80/50/0) that the tts app
  had been computing with only three tiers (50/DOT/entertainment; no 100% tier anywhere).
- Sources verified VERBATIM 2026-07-09: i1120s (2025) + i1065 (2025) "Special Rules â€” Travel,
  meals, and entertainment" (new excerpts on IRS_2025_1120S_INSTR_FULL / IRS_2025_I1065);
  **NEW source IRS_2025_PUB463** (Pub 463 (2025) ch. 2) carrying the six 100% exception
  categories (Â§274(n)(2)(A) â†’ Â§274(e)(2)/(3)/(4)/(7)/(8)/(9): compensation-treated, reimbursed
  Ã—2, recreational/social employee events, meals to the general public, meals sold) and the
  DOT "percentage is 80%" text. IRC_274 linked secondary (pre-existing source).
- `load_1120s_full.py`: 6 new PAGE1 facts (meals_100pct/dot_80pct/50pct/entertainment_0pct +
  the two worksheet outputs) Â· R009 deductible = 1.00/0.80/0.50/0.00 (Line 19 COMPONENT) Â·
  R010 nondeductible = 0.50/0.20/1.00 â†’ K16c/M-1 3b/M-2 5a Â· D004 warning (100% tier is
  exception-only) Â· four-tier scenario (7,800/8,200 on a 16,000 book total) Â· line-19 notes +
  source_rules Â· Sch K R016 description now tier-aware. TY2026 WATCH noted in R009: Â§274(o)
  employer-convenience meals disallowance applies to amounts paid after 12/31/2025.
- `load_1065_schedule_k.py`: mirrored on 1065_PAGE1 (p1_21_meals_* facts, R-1065P1-MEALS/
  -MEALSND â†’ Sch K 18c/M-1 4b, D_1065P1_MEALS100, scenario P1-5, line-21 notes); _load_sources
  now also picks up IRC_274/IRS_2025_PUB463 from the DB (run load_1120s_full first).
- SQLite-validated (scratch db_validate.sqlite3, both loaders; rules/facts/diags/scenarios
  checked in-DB) â†’ Supabase-seeded (TaxForms 121 / FA 550 â€” counts unchanged, amendment-only)
  â†’ deployed exports verified carrying R009/R010 + the 1065 pair â†’ tts mirrors refreshed
  (`server/specs/1120s_page1_spec.json` + `1065_page1_spec.json`). tts build same session
  (seed D_MEALS_100 + compute + UI + parity-fixture regen).

## 2026-07-09 â€” 1120S_SCHL R008: BOY-inventory no-prior-year default (Ken ruling)
- Ken ruled (tts s38, live): L3 BOY inventory carries from prior-year EOY (existing
  R006); ONLY when no prior-year return was prepared does it default from Form 1125-A
  line 1. Fill-blank-only; preparer entry always wins.
- Amended `load_1120s_complete.py` (SCHL block): +fact `f1125a_boy_inventory` (cross-form),
  +rule **R008** (conditional) w/ authority link (SCHL instr, secondary â€” practice logic,
  Ken ruling 2026-07-09), R006 description cross-references R008.
- SQLite-validated â†’ Supabase-seeded (upsert; R001-R008 confirmed) â†’ deployed
  `lookup/1120S_SCHL/export/` verified carrying R008 â†’ cached to tts as
  `server/specs/1120s_schl_spec.json`. tts implemented same session
  (`_default_l3a_from_cogs_db`, registry write-through; 4 DB tests; flow gate 447).

*One entry per session that touches Rule Studio. Newest first.
Created 2026-06-10 during the 1040 campaign Phase 0 state audit (this file did not previously exist).*

---

## 2026-07-12 — FA-2553-*/FA-2848-* ACTIVATED (the tts 2553+2848 print-unit pair landed, tts s69)
- The s66 one-motion recipe: both loaders' FLOW_ASSERTIONS flipped draft -> active
  (+ the harness draft-pins flipped to active-pins; 2553 + 2848 harnesses re-run
  ALL GREEN), both loaders re-run against RS prod (idempotent; status-only), the
  deployed FA exports verified (1120S 38 = 32 + the 6 new / 1065 40 / 1040 395),
  and all three tts gate mirrors refreshed from the deployed endpoint in the same
  motion (1120S verbatim / 1065 minus the s64 4 staged-pending / 1040 ADDITIVE
  append of the 3 FA-2848 only — the 1040 mirror's full rebase vs the 395-entry
  export is a tracked tts follow-up, DEFERRAL_AUDIT s69).
- tts runners: `_run_2553_assertion` (the three published i2553 window examples +
  the count gate + the no-8832 seam) + `_run_2848_assertion` (future-clock /
  45-60-day window / the CAFFILL 9-digit-or-'None' shape + autofill source pins);
  tts flow gate 463 -> 475 GREEN. WO-26/WO-27 marked DONE (Gate-2 shipped).

## 2026-07-09 â€” FA-ENT-8824-01 ACTIVATED (the tts entity-8824 unit landed, S6 unit 2)
*One-line status flip in `load_8824.py` (draft â†’ active), the FA-8941 recipe: the tts
engine now routes R-8824-ENTROUTE (entity 4797 L5/L16 via aggregate_dispositions,
Schedule D (1120-S) L5/L12 â†’ K7/K8a via aggregate_schedule_d), emits per-exchange
IRS8824 MeF documents, renders the entity packet copy, and covers the D_8824_* set on
entity returns. SQLite-validated (db_validate) â†’ Supabase seeded (FlowAssertions 550,
counts unchanged â€” status-only) â†’ deployed 1120S export verified (30 actives,
FA-ENT-8824-01 present). tts runner `_run_ent8824_assertion` added; gate 446â†’447.
NOTE for the queued reconciliation pass: the tts mirror stays PINNED (now 26 = prior
25 + this id); the export's s32-drift actives still lack runners. App-side boundary
beyond this spec (handoff): D_8824_011 (tts code-registered) REDs a 1065
capital-character exchange â€” R-8824-ENTROUTE names Schedule D (1065) L5/L12 but no
Schedule D (1065) aggregation/spec exists (K8/K9a preparer-entered); suggest an RS
amendment encoding that boundary (plus: entity Â§1043 = D_8824_010 escalates to error
app-side â€” spec is silent on entity Â§1043; ratify or amend).*

## 2026-07-08 (night) â€” S6 RS TRIO authored + seeded (Ken delegated with four in-session rulings)
*The tax-app Scenario-6 kickoff (s34) hit three RS gaps; Ken ruled the judgment calls live
(8941 line 5 preparer-entered Â· Â§280C diagnostic-only Â· 8824 = 1120S+1065 routing-only Â·
personal-property Â§1031 = hard RED + scenario override) and delegated the authoring.*
- **NEW `load_8941`** â€” Form 8941 Â§45R greenfield (lookup was 404). Sources VERBATIM: the
  in-hand f8941 2025 face (manifest-hashed tts copy) + i8941 2025 (fetched irs.gov, 30 pp).
  16 facts / 8 rules (ELIGÂ·WAGESÂ·CREDITÂ·FTEPHASEÂ·WAGEPHASEÂ·STATEÂ·DESTÂ·280C) / 23 lines /
  6 diagnostics / 4 scenarios / 2 STAGED FAs (FA-8941-01/02, draft â€” activate with the tts
  compute unit). entity_types [1120S,1065,1040,1120]; S corps stop at line 16 â†’ K13g.
  âš  TWO flags encoded, not resolved (tax-app REVIEW_QUEUE): (1) face $33,000/$67,000 vs
  i8941 WS6 $33,300 self-contradiction â†’ D_8941_005 hand-verify band; (2) the ATS S6 key
  INVERTS the WS5 FTE phaseout (prints the 12,753 REDUCTION as line 8; Â§45R(d)(3)(A) gives
  51,014) â€” scenario F8941-T1 pins the LAW, F8941-T2 documents the key as printed.
- **`load_8824` amended** â€” entity_types ['1040'] â†’ ['1040','1120S','1065'] (Ken ruling:
  routing-only). NEW `R-8824-ENTROUTE` (recognized capital â†’ Schedule D (1120-S/1065)
  lines 5/12 face-verbatim; L21/ordinary â†’ entity 4797 L16; Â§1231 â†’ 4797 L5; deferred gain
  = M-1 timing, never AAA/M-2; line 25 stays informational â€” Â§1.168(i)-6 = future unit).
  NEW scenario F8824-E1 (the ATS S6 truck: personal property â†’ D_8824_009 RED on a real
  return; key reproduced only via the tts documented-quirk override). FA-ENT-8824-01
  STAGED draft.
- **`load_1120s_specs`/`load_1120s_full` â€” SCHD_1120S renumbered to the 2025 face**
  (verified verbatim vs f1120ssd.pdf 2025 + IRS1120SScheduleD.xsd): QOF header + 1a
  direct/1b-3 = 8949 boxes/4 = 6252/5 = 8824/6 = tax-on-ST/**7 = net ST â†’ K7 or K10**;
  Part II 8a-15 (15 = net LT); Part III 16-23 (23 â†’ page-1 23b); R005 BIG chain corrected
  to the 16-23 lines; new inflow facts (6252/8824/cap-gain-distributions, QOF). R011/R012 +
  Schedule K R013/R014 corrected ("Line 5â†’K7" was pre-2025). **Stale pre-2025 line rows
  (1c/7a/7b/7c) DELETED in-loader** (update_or_create can't remove rows â€” the F4797-G2
  lesson, now self-healing). NOTE: the K-1 spec's "Box 7 â†’ Schedule D line 5" rows are the
  SHAREHOLDER'S 1040 Schedule D (correct) â€” left alone.
- SQLite-validated (scratch db_validate.sqlite3) Â· **Supabase-seeded (TaxForms 120â†’121,
  FlowAssertions â†’550)** Â· deployed exports verified (8941 rules+T1 51,014 pin; 8824
  entity_types+ENTROUTE+E1; SCHD 2025 line set + R011 "Line 7 -> K Line 7") Â· tts mirrors
  refreshed (8941_spec.json NEW Â· form_8824_spec.json Â· sched_d_1120s_spec.json).
- Retraction: the s34 handoff's "diagnostics/tests export null ids" claim was a wrong-key
  dump artifact (the export's diagnostic_id/scenario_name fields are fine).

## 2026-07-08 (evening) â€” K1_1120S ROUNDING LEG + GA501 drift amendments seeded
*Same session as the 4797 entity leg below (the Ken-set non-e-help queue).*
- **K1_1120S rounding (Ken ruling: residual-offset allocator):** NEW rule `R-K1-ROUND` â€”
  whole-dollar half-up per shareholder, the ROUNDING RESIDUAL to the LAST shareholder
  (canonical K-1 order) so Î£ K-1 == Schedule K EXACTLY (Â§1377(a) + the ATS S5 key's
  1,788/1,787 Â· 5,732/5,731 behavior; the spec was silent on rounding). + scenario
  "Residual-offset rounding" + links (IRC_1377 primary). NEW FA `FA-K1-ROUND` in
  seed_flow_assertions (entity_types 1120S). Seeded; deployed export verified
  (R-K1-ROUND + scenario served). tts build = the k1_issuer leg (same session).
- **GA501 (the 2026-07-08_ga501_spec_drift.md handoff, all three items):**
  (1) `D_GA501_CONFORM`/`D_GA501_DEPR` texts amended to the HB 1199 ruling (GA conforms
  to OBBBA Â§179 $2.5M/$4M; decouples ONLY from Â§168(k)/(n) bonus) â€” mirrors the
  Ken-approved rules_ga700/rules_ga501 wording; (2) line_map extended 15â†’27 lines
  (9c credit cap + the page-2 settle block 11a-20, face verbatim Rev. 07/09/25) with
  amended `R-GA501-CREDITS` (routes through 9c) + NEW `R-GA501-SETTLE` + 6 new input
  facts + scenario GA501-T6 (9c cap + refund path 449/433); (3) face-mechanics notes
  were already carried in the tts render. Seeded; deployed export verified (27 lines,
  R-GA501-SETTLE, HB 1199 text); tts mirror `server/specs/ga501_spec.json` refreshed +
  T6 transcribed as a pure pin (`test_spec_t6_settle_block_refund_path`, 17/17).

## 2026-07-08 (evening) â€” 4797 ENTITY PASS-THROUGH LEG authored + seeded (Ken ruling: "build the full unit")
*The Â§179-disposition pass-through gap found in the tts S5 mapper build (REVIEW_QUEUE 2026-07-08);
Ken ruled build-the-full-unit on the recommended option. Spec-first â€” this is the RS leg.*
- **Law verified verbatim 2026-07-08** (live i4797 HTML + i1120s PDF p.15/41 + i1065 PDF p.20/52,
  pymupdf): i4797 "Partnerships and S corporations do not report these transactions on Form 4797,
  4684, 6252, or 8824â€¦"; i1120s line 4 â†’ K-1 box 17 code K + the 8-item PRO-RATA statement list;
  i1065 line 6 â†’ box 20 code L; i1120s M-2 adjustment 1 (AAA increase by income) = the 3a
  other-addition home for the corp-level gain.
- **load_4797 amended** (in-loader â€” this loader preserves entity_types on every seed):
  NEW rule `R-4797-ENTPASS` (routing; per-property `f4797_sec179_passthrough` excludes the property
  from EVERY 4797 line; outputs `f4797_ent179_gain/price/cost/s179` â€” the statement dataset +
  the AAA 3a addition) Â· NEW diagnostic `D_4797_ENTPASS` (info, never-silent) Â· 2 new facts +
  4 output facts Â· scenarios F4797-E1/E2 (the ATS S5 Dodge-truck numbers: gain 1,400, statement
  cost 1,000 EXCLUDING Â§179, Â§179 1,000) Â· NEW source `IRS_2025_1065_INSTR` + excerpts on
  `IRS_2025_4797_INSTR`/`IRS_2025_1120S_INSTR` Â· 2 new FAs `FA-ENT-4797-179` (1120S+1065
  exclusion + Î£ pro-rata = entity totals) / `FA-1120S-M2-179` (gain â†’ M-2 3a).
- **KEY-QUIRK NOTE encoded in the rule:** the ATS S5 key prints FULL facts on EACH 50% K-1 and
  2Ã—gain (2,800) on M-2 3a â€” contradicts the i1120s verbatim "pro rata share" + Â§1377(a); the
  spec encodes the LAW (pro-rata per owner, gain enters AAA once). Owner-side 1040 reporting
  from K-1 17K facts = stated follow-up unit.
- `check_4797_integrity.py` extended (own transcription of the exclusion) â€” **ALL CHECKS PASS**
  (33 facts / 9 rules / 15 diagnostics / 22 scenarios / 9 FAs). **Seeded RS Supabase**
  (FlowAssertions 539â†’541); **deployed export verified** (R-4797-ENTPASS + D_4797_ENTPASS +
  the 6 new facts + E1/E2 all served); tts canonical `server/specs/4797_spec.json` refreshed.
- Pre-existing drift noted, not touched: the export still serves the stale `F4797-G2` scenario
  row (removed from the loader 2026-06-28; seeder can't delete DB rows).

## 2026-07-08 â€” 1041 flow-assertion family CONSOLIDATED + ACTIVATED (S-11 leg 8a, Ken-approved)
*Ken green-lit the tax-app REVIEW_QUEUE authoring plan ("go ahead with the 1041 FA authoring plan").*
- **Root cause of the "zero 1041 FAs" export:** the 2026-07-05 S-11 authoring HAD staged 10 draft
  FlowAssertions (spine: DNI/IDD/TIERS/EXEMPT/TAX/NIIT Â· K-1: CHAR/RECON/FINYR/NIIT) â€” none ever
  activated, and the export serves active-only. The tax-app leg-8 gate build surfaced it.
- **NEW `load_1041_flow_assertions.py` = the single FA home for the 1041 family** (17 active +
  2 staged), transcribed from the approved R-1041-*/R-K1041-* rules (no new tax law): page-1
  chains (TOTINC/ATI/TAXINC/TOTTAX/SETTLE) Â· Subchapter J core (DNI incl. the corpus-gain
  back-out, IDD smaller-of, Â§662 TIERS) Â· Â§642(b) EXEMPT table Â· Â§1(e) RATES + CGRATE 0/15/20
  stacking pins (RP 2024-40) Â· ESBT 37% Â· K-1 CHAR/SUM/FINYR Â· GATE-1041-DEFERS (AMT/bankruptcy
  RED-defers + grantor-no-K-1) Â· FA-1041-GA501 (state base = federal ATI).
- **Reconciliation:** ids shared with the drafts re-authored + FORCE-ACTIVE (the load_sch_1a
  precedent); FA-K1041-FINYR adopted active (engine-backed); **FA-1041-TAX + FA-K1041-RECON
  DISABLED** (superseded by RATES+CGRATE / SUM â€” supersession note prepended to description);
  **FA-1041-NIIT + FA-K1041-NIIT stay STAGED** (trust-side 8960 + the box-14Hâ†’8960-L7 import
  are unbuilt). FA blocks REMOVED from load_1041_spine / load_1041_schedule_k1 (tombstoned) so
  a reseed can't regress statuses; the k1 loader's hollow-seed guard no longer requires FAs.
- Validated on throwaway SQLite (`scratchpad/validate_1041_fa.py` â€” 17 active + 2 staged,
  ids â‰¤ varchar(20), idempotent). **Seeded RS Supabase** (539 total â€” the 10 drafts updated in
  place + 9 new rows). **Deployed export verified:** `entity_type=1041` serves exactly the 17
  actives.
- tts side (same session): export cached as canonical `server/specs/flow_assertions_1041.json`;
  17 pure runners registered (`_RUNNERS_1041`) exercising compute_1041 / rate_schedule_tax /
  capital_gain_tax / allocate_k1_boxes / compute_ga501; full gate **422 â†’ 440**. â†’ the 1041
  form's last buildable leg closed; S-11 fully ticks on the app side.

## 2026-07-05 â€” SC1040 spec hygiene fix (promote to active + correct the $50k test pin)
During the tts-app SC1040 build (S-7), two hygiene issues surfaced in `load_sc1040.py`:
- **`FORM_STATUS` `draft` â†’ `active`** â€” the spec was fully authored + Ken-approved 2026-07-04
  (`READY_TO_SEED = True`), only the status label lagged.
- **Test scenario "SC resident, wages only, single, no dependents" pin corrected** â€” the
  `expected_outputs` L6 was the rough placeholder string `"SC1040TT lookup (~6% marginal at top;
  â‰ˆ $2,533)"`, which is WRONG. The published **SC1040TT_2025 row for $50,000-$50,050 = $2,360**
  (the table applies the 3-bracket structure to each $50-bracket MIDPOINT: 6%Ã—$50,025 âˆ’ 642 =
  2359.50 â†’ $2,360 half-up). The tts engine reproduces the published table **138/138 rows, zero
  mismatches** (verified vs the SCDOR PDF). Pin is now numeric `2360` + an explanatory note.
- **Re-seeded RS Supabase** (`manage.py load_sc1040`, idempotent update_or_create) â€” deployed
  `lookup/SC1040/export/` now returns `status: active` + `L6: 2360` (verified live, HTTP 200).
- No tax-law change; the rules/line_map/diagnostics were already correct (the tts four-leg app was
  built from them). `SC_SCHEDULE_NR` re-seeded alongside (unchanged).

## 2026-07-05 â€” GA-500 military-exclusion reconciliation debt CLOSED (RS side) â€” spec authoritative, app over-inclusive
*Picked up the BUILD_ORDER "open reconciliation debt" as a bounded close after S-5/S-6. The debt framed it as
"the app should not stay ahead of the law" â€” the gap-check + research showed the REVERSE.*
- **Gap-check:** `load_ga500_form_500.py` already fully models the military exclusion â€” `GA_MILITARY_RIE_BASE
  {2025:17500}` / `GA_MILITARY_RIE_MAX {2025:35000}` + a verbatim IT-511 Sch 1 p3 worksheet excerpt (under-62;
  base $17,500; +$17,500 once GA earned income â‰¥ $17,501; max $35,000). The RS spec was NOT behind.
- **Research-verified (2025 IT-511 p.21, Form 500 Sch 1 p3, O.C.G.A. Â§48-7-27(a)(5.1)(A)):** the RS rule is
  correct. The app's 7/5 `min(mret, 35000)` is OVER-inclusive â€” wrong 3 ways: ignores the under-62 age gate
  (grants it at any age), ignores the earned-income condition on the second $17,500, and the base tranche
  alone caps at $17,500 not $35,000. A 62+ taxpayer's military pay is handled by the GENERAL retirement
  exclusion ($35k 62-64 / $65k 65+), not the military one â€” the two are age-segregated, never stacked.
- **SB 31 year-keyed find:** GA SB 31 (2025 session) fully exempts military retirement regardless of age/income
  for **taxable years beginning on/after Jan 1, 2026** â€” does NOT reach TY2025. So the RS spec correctly keeps
  the HB 1064 structure for 2025; the loader's 2026 military placeholder (17,500/35,000) is STALE for TY2026.
- **Resolution (spec-first):** no RS TY2025 spec change (already correct); annotated the loader with a
  year-keyed SB 31 warning (comment only â€” no seeded field changed, so no reseed); **spawned tts task
  `task_f550dfd2`** to fix the app compute to the worksheet logic. Closed the debt in BUILD_ORDER.
  Reinforces the front-door value: the spec-vs-app reconciliation caught that the APP had drifted, not the spec.

## 2026-07-05 â€” S-5 boundary diagnostics AUTHORED + SEEDED + EXPORTED (WO-04) â€” consolidated ENTITY_BOUNDARY form
*Ken opened S-5 right after S-6. Second full front-door loop the same day. PRODUCT_MAP Â§17: Core never goes
silent at a module boundary â€” it must DETECT and throw a loud RED diagnostic.*
- **Gap-check finding:** 4 of 5 boundaries already existed as on-form RED-defers (D_L_M3 on 1065_L; D_SCHK_K3
  + D_SCHK_704C on SCH_K_1065; Sch B Q10 Â§754 on 1065_B). But D_SCHK_K3 was a **blanket "international out of
  scope" flag** â€” PRODUCT_MAP makes the **DFE determination** ("record WHY K-2/K-3 aren't required") Core season
  one. Real gaps = the K-2/K-3 DFE gate + a multistate-apportionment indicator.
- **Authorities verified (research pass, NOT memory):** M-3 (Instr. Sch. M-3 1065 Rev. 11/2023 = $10M assets /
  $35M receipts / 50% REP; 1120-S Rev. 12/2019 = $10M assets single test); K-2/K-3 DFE 4 criteria (2025 i1065
  K-2/K-3); Â§704(c)/Treas. Reg. Â§1.704-3; Â§754/Â§743(d)/Â§734(d) ($250k substantial built-in loss / basis
  reduction); P.L. 86-272 (15 U.S.C. Â§381). OBBBA changed none of these.
- **Scope (Ken, all recommended):** SHAPE = a **new consolidated `ENTITY_BOUNDARY` form** (single completeness
  critic, not scattered amendments); K-2/K-3 = **COMPUTE the 4-criteria DFE gate** (RED D_EB_K2K3 on fail +
  D_EB_DFE_OK info recording the basis); apportionment = **indicator** (+ P.L. 86-272 note, state-specific);
  M-3/Â§754/Â§704(c) = **re-encode with pinned thresholds** (existing on-form flags remain).
- **Authored** `load_entity_boundary.py` â€” form `ENTITY_BOUNDARY` (entity_types 1065/1120S), 23 facts / 5 rules
  / 5 lines / 6 diagnostics / 10 scenarios / 3 FA. **6 self-owned authority sources** (IRS_2025_M3_1065,
  IRS_2025_M3_1120S, IRS_2025_K2K3_1065, TREAS_REG_704_3, IRC_754_743_734, PL_86_272) so it reconstructs
  standalone (no cross-loader source dependency). Auto-discovered by seed_all phase 2.
- **Validated** on throwaway SQLite (`scratchpad/validate_boundary.py`): form seeded, all rules/diags present,
  ALL rules cited, CharField caps introspected-and-clean, M-3 (both entity branches) + DFE (all-met / K-3-request
  / foreign-tax>$300) logic spot-checked. ALL PASS.
- **Ken review walk â†’ "Approve â€” flip, seed, export."** Flipped READY_TO_SEED, seeded to prod (95â†’**96 TaxForms
  / 457 FlowAssertions / 830 FormRules**), verified `lookup/ENTITY_BOUNDARY/export/` = **200**. BUILD_ORDER S-5
  ticked [RS]âœ…â†’[APP]â¬œ, NEXT authoring advanced to S-11 (1041). Explicit-path commits.
- **Caveats carried to the tts build:** (1) M-3 instruction sets aren't reissued annually (1065 Rev 11/2023,
  1120-S Rev 12/2019 control TY2025 â€” thresholds unchanged; re-confirm each season). (2) B5 apportionment is
  state-specific â€” P.L. 86-272 is the only federal anchor; per-state nexus thresholds pulled/verified per state.
- **RS authoring spine now clear to S-11:** S-4 (1065 core), S-5 (boundary diagnostics), S-6 (PAL/basis) all DONE.

## 2026-07-05 â€” S-6 PAL/basis deepening AUTHORED + SEEDED + EXPORTED (WO-03) â€” first full front-door loop
*Ken opened S-6 through the new front door ("finish the new procedure implementation" â†’ picked S-6 PAL/basis).
The whole WORK_ORDERS pipeline ran once, end-to-end, as designed. No prod risk until the review-walk approval.*
- **Front-door loop (all transitions logged in WORK_ORDERS.md):** GAP-CHECKED (R1-R4 = amendments to the
  existing FORM_8582/SCHEDULE_E; R5 Â§461(l) = the one real gap) â†’ research-verify (background agent, verbatim
  vs primary sources) â†’ `pal_basis_source_brief.md` â†’ Gate-1 scope walk (4 AskUserQuestion) â†’ author â†’
  SQLite-validate â†’ Ken review walk â†’ flip + seed + export.
- **Authorities verified (research pass, NOT memory):** R1 self-rental Treas. Reg. Â§1.469-2(f)(6); R2 PTP IRC
  Â§469(k); R3 REP Â§469(c)(7) + Treas. Reg. Â§1.469-9; R4 at-risk Â§465 + Reg. Â§1.469-2T(d)(6) ordering; R5
  Â§461(l) + Rev. Proc. 2024-40 + i461 (2025). 2025 EBL thresholds **$313,000 / $626,000** (Rev. Proc. 2024-40,
  confirmed verbatim by i461). OBBBA made Â§461(l) permanent; disallowed EBL â†’ NOL carryover (the "retest"
  alternative was NON-enacted â€” flagged year-keyed).
- **Scope (Ken, all recommended):** R1+R2 COMPUTE (self-rental net-income recharacterization item-by-item, loss
  stays passive; PTP segregated off-8582, per-PTP, freed on full disposition); R3 REP **upgraded the 2026-06-13
  RED-defer â†’ checkbox + Â§1.469-9(g) election flag** (D_8582_RE_PRO errorâ†’info; the two tests preparer-asserted
  + sanity-checked via D_8582_REP_TESTS; D_8582_REP_MATLPART reminds each un-aggregated rental needs material
  participation); R4 at-risk = diagnostic-only (D_8582_ATRISK, ordering Â§465â†’Â§469â†’Â§461(l), route to 6198); R5
  = new Form `461` diagnostic (computes EBL + flags; pinned thresholds; NOL described-not-built).
- **Authored:** R1-R4 amend the HOME loader `load_1040_schedule_e.py` (reconstructable â€” replays in seed_all
  phase 2); R5 = new `load_1040_form_461.py` (auto-discovered by seed_all). New authorities: TREAS_REG_469,
  IRC_465, IRC_461, IRS_2025_F461_INSTR, REV_PROC_2024_40; Â§469(k)/Â§469(c)(7) excerpts added to IRC_469.
- **Validated** on throwaway SQLite (`scratchpad/validate_pal.py`): 3 forms seeded, all new rules/diags present,
  D_8582_RE_PRO upgraded, ALL rules cited, CharField caps introspected-and-clean, EBL math spot-checked. ALL PASS.
- **Ken review walk (W1-W5) â†’ "Approve â€” flip, seed, export."** Flipped Form 461 `READY_TO_SEED`, seeded both
  loaders to prod (94â†’**95 TaxForms / 454 FlowAssertions / 825 FormRules**), verified `lookup/{FORM_8582,
  SCHEDULE_E,461}/export/` all **200** (in-process test client, read-only). BUILD_ORDER S-6 ticked [RS]âœ…â†’[APP]â¬œ
  (tts-tax-status), NEXT authoring advanced to S-5. Explicit-path commits (shared worktree).
- **Two caveats carried to the tts build (flagged, not guessed):** (1) Form 461 FACE line-numbering was mapped
  to the Â§461(l)(3) mechanic (BIZ-INC/BIZ-DED/THRESH/EBL/NOL), NOT the printed 2025 Part I-III positions â€”
  i461 `requires_human_review`; confirm before the app build. (2) disallowed-EBLâ†’NOL is year-keyed.

## 2026-07-05 â€” WORK_ORDERS front-door adopted + BUILD_ORDER-driven; caught a cross-session stale "author Schedule K" loop
*Ken + chat were setting up "a more automated orderly process" (the WORK_ORDERS front door) and, across three
prompts, kept instructing "author 1065 core, Schedule K first." A parallel tts/app session was editing the
shared brain concurrently. No spec authored this session â€” it was process plumbing + a reconciliation fix.*
- **Root finding â€” the instruction was stale, thrice.** 1065-core RS authoring is COMPLETE (2026-07-04): all
  6 forms seeded+exported (200) â€” Schedule K spine (`1065_PAGE1`+`SCH_K_1065`), K-1+alloc, M-1/M-2, L/B;
  8825/4562/3800 cover 1065; 7-form batch in `approved_specs.py`. Verified on-disk (`load_1065_*.py` +
  `exports/form_sch_k_1065/`) + live STATUS. Running the gap-check on Schedule K returned "exists (200)" â€”
  the front door working as designed (it CAUGHT the would-be duplicate). Same over-completion on WO-01 (4835/
  8835/8936 all done) + the four state specs.
- **The drift's source.** BUILD_ORDER.md (canonical in `tts-tax-status`) â€” placed by the parallel session
  (`b54c111`) â€” carried a stale `S-4 Â· 1065 core â€¦ untouched beyond SE`, all schedule boxes unticked, and a
  `â–¶ NEXT authoring = Schedule K [RS/Ken]` line, *despite* a header claiming the marks were reconciled to live
  STATUS. Both sessions inherited the stale line and talked past each other through it.
- **Files placed/edited (RS repo, `9a062cb`):** replaced WORK_ORDERS.md with the provided BUILD_ORDER-driven
  version (front-door MECHANISM only â€” gap-check + transitions + Gate-1; NO independent backlog, sequence
  lives in the SPINE), reconciled to live STATUS (WO-01 4835 + WO-02 1065-core DONE; SC1040/AL40/NC-D400/GA700
  AUTHORED). CLAUDE.md: boot line (pull tts-tax-status; BUILD_ORDER=order / SEASON_PLAN=gates / PRODUCT_MAP=scope)
  + standing rule "update WORK_ORDERS at every transition; the queue is the record."
- **Fixed the canonical source (tts-tax-status `5c57886`).** BUILD_ORDER S-4 â†’ `[RS]âœ…â†’[APP]â¬œ` (schedules
  ticked DONE 2026-07-04; remaining = issuer-side 1065 K-1 persistence â†’ 1040 import + tts compute build);
  `â–¶ NEXT authoring` advanced off Schedule K to **S-5 boundary diagnostics / S-6 PALÂ·basis** (S-6 before the
  regression bed locks). Zip's BUILD_ORDER/PRODUCT_MAP were already committed by the parallel session; left
  SEASON_PLAN.md as re-cut by that session (not replaced).
- **Coordination risk noted:** the tts session is only paused mid-migration; the S-4 fix is on origin so a
  pull-before-edit there carries it, but watch for a re-cut reverting it.
- **Memory:** added `rs-1065-core-done-buildorder-stale` (don't re-author Schedule K; seed SPINE status from
  live STATUS, not draft checkboxes) + MEMORY.md index line. Explicit-path commits throughout (shared worktree).

## 2026-07-05 â€” 1120-S delta audit COMPLETE (prod â†” rebuild 0-delta)
*Ken: "lets start the delta audit" (declined a context clear â€” the audit overlapped fresh GA-700 context).
Closed the deferred reconstructability drift from the 2026-07-04 check. Clear of the parallel session
(explicit-path commits).*
- **Method:** fresh-SQLite `seed_all` rebuild + per-form rule_id diff vs prod (`scratchpad/rebuild_diff.py`,
  `dump_rules.py`, `dump_forms.py`). Dispatched an Explore agent to map the 5-loader 1120-S landscape â€” but
  its intent verdicts ("R010-18 reproducible", "8283/8949 intentional multi-entity") were **REFUTED by the
  empirical rebuild**; the diff was decisive, not the code-read. Lesson: verify loader-provenance claims
  against an actual rebuild.
- **Â§A â€” ORDERING BUG (not orphans).** `load_1120s_full` amends `SCH_K_1120S`/`SCHD_1120S` (adds R010-18/
  R010-12) but ran alphabetically in phase 2 BEFORE its base `load_1120s_specs`; its `.first()` lookup
  returned None â†’ rules silently dropped on rebuild (rebuild had 8/5, prod 17/8). **Fix:** moved it to
  `seed_all` `AMEND_LOADERS` (phase 3) â†’ rebuild reproduces 17/8. **Zero prod change** (prod already had them).
- **Â§B/Â§D â€” LOADER POLLUTION.** `load_1120s_complete` (`_load_8995/8995a/8582/8283`) + `load_1120s_specs`
  (`_load_form_8949`) re-seeded 1040-owned forms with duplicate R001-R00x sets prod never had + fabricated a
  bare `8582`. Confirmed the 1040 primaries own these (multi-entity types set there). **Removed the 5 blocks**
  (466 + 122 lines, assertion-guarded scripts). **Zero prod change** â€” prod was clean; pollution was rebuild-only.
- **Â§C-new â€” 4797 v1 empty stub.** The last prod-vs-rebuild gap (prod 93 rows vs rebuild 92): a 0-rule v1
  version left when the 2026-07-04 check deleted 4797's orphan rules but not the emptied row (export serves
  v2, 8 rules). Ken approved delete â†’ snapshot-backed removal (`remediation_snapshot_4797_v1.json`; v1 also
  carried 19 stale facts/22 lines/5 diag/6 scenarios that cascaded). Prod 93 â†’ **92**.
- **Bonus (DECISIONS D-8) â€” GA600S content correction.** The GA S-corp spec (`load_remaining_1120s`) had a
  **stale 5.49% PTET rate with a LIVE compute `* 0.0549`** + a **3-factor apportionment formula** â€” both wrong
  for 2025. Corrected to **5.19%** (Form 600S Rev. 09/11/25) + the **single gross-receipts factor** (Â§48-7-31),
  verified via the GA-700 research; the PTET scenario `$200K Ã— 5.49% = $10,980` â†’ `Ã— 5.19% = $10,380`. Reseeded;
  `lookup/GA600S/export/` = 200 (R003 `*0.0519`, R005 single-factor, ptet_rate 5.19).
- **RESULT:** prod â†” a fresh rebuild is **0-delta** â€” 92 form_numbers, 0 form-set diff, 0 rule-level diff.
  Prod **92 TaxForms / 441 FlowAssertions / 801 FormRules**. Loader fixes committed `5f46311`; docs updated
  (`reconstructability_check.md` banner + Remaining-order item 2 âœ…; STATUS Known-issues resolved). The
  standing check (rebuild + diff) is documented for periodic re-run.

## 2026-07-05 â€” GA Form 700 + PTET AUTHORED + SEEDED + EXPORTED (August state track, form 4 â€” track COMPLETE)
*Ken picked GA-700 + PTET as the next thread (AskUserQuestion). 1st partnership-entity state spec; GA600S
(S-corp, load_remaining_1120s.py) is the closest GA entity precedent. Clear of the parallel session
(explicit-path commits).*
- **Research (subagent, verbatim from the FINAL 2025 GA DOR sources â€” Form 700 Rev. 09/11/25; IT-711
  booklet; HB 149 PTET FAQ; Reg. 560-7-3-.03):** flat/PTET rate **5.19%** (2025; 2026â†’4.99%); PTET (HB 149)
  = annual irrevocable page-1 election, entity-level base (federal taxable income â†’ Â§48-7-27 â†’ Â§48-7-31
  apportionment, NOT a resident/nonresident split) Ã— 5.19%; owners exclude via **PTEDED/PTEADD** on Form
  500, no owner credit, credits/NOLs stay with the entity. **Single gross-receipts apportionment** (6
  decimals, since 2008). GA decouples from Â§168(k)/OBBBA â€” add back federal depr (Sch 5 L7), subtract GA
  Form 4562 depr (Sch 6 L4); **GA Â§179 $1.05M/$2.62M**. **4% nonresident withholding** (<$1,000 exempt,
  G-2-A; displaced by PTET). Partnerships exempt from GA net worth tax.
- **Caught two stale values in the existing GA600S loader** (research cross-check): PTET rate **5.49%**
  (should be 5.19%) and **"property/payroll/sales" 3-factor** apportionment (GA is single-factor). GA700
  pins the correct values; GA600S correction logged to DECISIONS D-8 + the 1120-S delta audit.
- **Source brief** `ga700_source_brief.md` + **scope walk** (4 AskUserQuestion, all maximal â€” DECISIONS
  **D-8**): A full PTET compute; B compute the Â§179 delta + structure, direct-entry the GA-4562 figures;
  C compute Sch 4 partner allocation + 4% NRW; D direct-entry Sch 10 credits, RED-defer NOL/composite/UET.
- **Authored `load_ga700.py`** (SC1040/NC-D400 pattern). **Validated on throwaway SQLite** via
  `scratchpad/validate_ga.py` (CharField caps clean; all 11 rules cited). **Review walk (W1-W6)** â€” Jan 1
  2024 conformity (re-verify the 2025 bill), 5.19% rate (+5.75% reg quirk in the RED-deferred UET),
  entity-level PTET base, Â§179 figures, single-factor apportionment, Sch 4 partner model â€” all blessed.
  Ken: "Approve â€” flip, seed, export."
- **SEEDED + EXPORTED:** prod **92 â†’ 93 TaxForms / 436 â†’ 441 FlowAssertions** (+GA700, draft, entity
  ['1065']); `lookup/GA700/export/` = **HTTP 200** (verified live). 22 facts / 11 rules / 20 lines / 10
  diag / 7 tests / 5 FA; 5 GA sources. **The August state track (SC1040/AL-40/NC-D400/GA-700) is COMPLETE.**
  Next: the 1120-S delta audit (incl. the GA600S 5.49%/3-factor correction).

## 2026-07-04 â€” RS spec cleanup handoff (5 forms brought to parity with tts builds)
*Carried "RS follow-ups" from tts STATUS (twelfth session): tts code is already correct/self-consistent;
this session brought the RS SPECS + the re-exported tts spec mirrors into parity. Ground rules: amend the
HOME loader's data lists + re-run (reconstructable), keep id fields â‰¤ 20 chars, extend the enumerated
lists. Item 6 (3800 J4 Â§6417/Â§6418) = NO ACTION (documented intentional divergence). Clear of the
parallel session (explicit-path commits).*
- **Item 1 â€” FORM_8911 (Form 3800 now built).** Retired D_8911_004 (FormDiagnostic has no is_active field
  â†’ severity errorâ†’info + RETIRED reword, the RS equivalent of tts is_active=False); repointed
  FA-1040-8911-04 from the gating red_fires check to the new flow_check (line 3 â†’ 3800 Part III row 1s â†’
  Sch 3 line 6a after Â§38(c)); rewrote R-8911-SCHA-BUS + line 3 + fact notes + metadata + topic + docstring
  from "unbuilt/RED-deferred" to the built flow; dropped the now-retired D_8911_004:True from scenarios
  8911-T6/T7. Historical 2026-07-02 review-walk records left intact. Reseeded; export 200. Commit 14c7b5d.
- **Item 2 â€” 8936 / 8936_SCHA.** Extended D_8936_004 (on 8936_SCHA) from blank-VIN/PIS to also fire on a
  PIS date not in the return tax year (PIS-year credit); added R-8936-TRANSFER (FORM_8936, cited) â€” a
  qualifying dealer-transferred credit was received at POS, stops on Sch A (8c/8d/13b/13c), never re-lands
  on Sch 3, only a DENIED transfer repays (Sch 2 1b/1c); + D_8936_008 info + FA-1040-8936-06 (RS home for
  the transfer-STOP). Reseeded; exports 200; FA 435â†’436. Commit 0deee03.
- **Item 3 â€” 8949 (via load_1040_schedule_d).** Added D_8949_006 (error) â€” imported/YELLOW Exception-2
  summary rows start unconfirmed and must be preparer-reviewed pre-file (manual/GREEN untouched) + the
  grounding fact ct_import_confirmed (mirrors tts CapitalTransaction.import_confirmed, mig 0160). The
  loader's retire-stale prune keeps both. Reseeded; export 200. Commit 39dbb10.
- **Item 4 â€” SCHEDULE_A.** Added scha_qualified_contributions_cash â€” input-only, drives the line-11
  dotted annotation + the e-file qualifiedContributionsAmt attribute, affects no computed line (tts mig
  0159). Reseeded; export 200. Commit 30f73ff.
- **Item 5 â€” 8995 (via load_1040_schedule_c).** Recorded D_8995_001's retirement (8995-A now computes
  every above-threshold + patron return): severity errorâ†’info + RETIRED-DORMANT reword; R-8995-SCOPE
  formula/description + docstring + FA-1040-8995-03 from RED-defer â†’ routes to the COMPUTED 8995-A;
  scenario 8995-T5 expected D_8995_001 Trueâ†’False. Reseeded; export 200. Commit 5647024.
- **tts spec mirrors REFRESHED + COMMITTED + PUSHED** (tts 2ab9dae): re-exported 8911_spec / 8936_spec /
  8936_scha_spec / 8949_spec / schedule_a_spec / 8995_spec into tts-tax-app/server/specs/, format matched
  per file (5 compact from the RS endpoint; 8949 is indent=1/CRLF â€” regenerated to match, clean 23+/5âˆ’ diff).
- **DEFERRED to a tts session (flagged, not done):** (1) tts `flow_assertions_1040.json` FA gate reconcile
  (FA-1040-8911-04 update + FA-1040-8936-06 insert) â€” the file is CRLF/no-trailing-newline/hand-managed
  (its assertion_count already drifts from length) and feeds test_flow_assertions.py; the FA HOME (the RS
  loaders) is updated + committed, so the tts session should regenerate it with its own tooling. Also the
  duplicate `form_8949_spec.json` (export_rule_studio.py 1120-S tool, pretty). (2) Run the tts test suite
  to reconcile any paired seed-leg/diagnostic-count assertions (tts owns the suite + the DB-collision
  playbook). Note: RS FA-1040-8936-05 = "unused personal LOST" (matches tts -05); the transfer STOP is the
  new -06 (the handoff's "-05 pins it" was imprecise).

## 2026-07-04 â€” NC D-400 AUTHORED + SEEDED + EXPORTED (August state track, form 3)
*Ken: "next up." 4th state individual spec (GA-500/SC1040/AL-40 precedents). NC starts from FEDERAL AGI
(like GA-500) at a FLAT 4.25% rate â€” simpler than AL; complexity is the Schedule S depreciation add-back
(Ken's specialty) + the child-deduction table. Clear of the parallel session (explicit-path commits).*
- **Research (subagent, verbatim from the FINAL 2025 NCDOR PDFs â€” Form D-400 + Schedule S rev "Web-Fill
  9-25"; D-401 booklet 2025; cited Â§105-153.5/.6/.7):** flat **4.25%** (0.0425; TY2026â†’3.99%); std ded
  $12,750/$25,500/$19,125 (MFS $0 if spouse itemizes; no 65+/blind add-on); federal-AGI start (L6) â†’
  Sch S Part A additions (L7) / Part B deductions (L9) â†’ child deduction (AGI table $3,000â†’$0) + std/
  itemized â†’ NC taxable income (L14) â†’ flat tax. **Depreciation:** NC decoupled â€” add back **85%** of
  federal bonus (Part A L3) + 85% of the Â§179 excess over NC's **$25k/$200k** limits (L4); 20% recovery
  over 5 years (L23/24 reference 2020-24 add-backs). Conformity frozen **Jan 1 2023** (OBBBA not adopted).
- **Source brief** `nc_d400_source_brief.md` + **scope walk** (4 AskUserQuestion, all maximal â€” DECISIONS
  **D-7**): A resident + **Schedule PN** proration (L13â†’L14); B **COMPUTE** the current-year 85% bonus +
  85% Â§179-excess add-back, direct-entry the prior-year 20% installments (the $200k Â§179 phaseout is a
  diagnostic, not silently computed); C **structured** Part B subtractions (L18 US-obligation / L19 SS-RR
  / L20 Bailey / L21 military) with eligibility diagnostics; D direct-entry D-400TC/use-tax/contributions,
  RED-defer Schedule PN-1 / amended lines / L26e underpayment / L39 NC NOL.
- **Authored `load_nc_d400.py`** (AL-40/SC1040 pattern). **Validated on throwaway SQLite** via a reusable
  `scratchpad/validate_nc.py` harness that ALSO enforces the Postgres CharField caps SQLite ignores â€” it
  **CAUGHT `D_NCD400_179_PHASEOUT`=21 > the 20-char `diagnostic_id` cap** pre-seed (shortened to
  `D_NCD400_179LIMIT`), and flagged 3 pure-arithmetic rules with no authority link (grounded them to the
  D-400 face). **Review walk (W1-W6)** â€” flat rate, 85% add-back + limits, Jan-1-2023 conformity, std
  ded, child table, statute-provenance â€” all blessed. Ken: "Approve â€” flip, seed, export."
- **SEEDED + EXPORTED:** prod **91 â†’ 92 TaxForms / 431 â†’ 435 FlowAssertions** (+NC_D400, draft);
  `lookup/NC_D400/export/` = **HTTP 200** (verified live). 29 facts / 11 rules / 21 lines / 8 diag /
  8 tests / 4 flow assertions; 6 sources (5 NC + federal 1040), every rule cited. Next state form: GA-700 + PTET.

## 2026-07-04 â€” AL Form 40 AUTHORED + SEEDED + EXPORTED (August state track, form 2)
*Ken: "kick off AL Form 40." 3rd state individual spec (GA-500/SC1040 precedents). The checklist
flagged AL's federal-income-tax-deduction quirk as "the longest walk." Clear of the parallel session.*
- **Research (subagent, verbatim from the FINAL 2025 AL DOR PDFs â€” Form 40 25f40blk, booklet 25f40bk
  incl. the p.31 FIT worksheet + p.8 std-ded chart, Â§40-18-5/Â§40-18-15):** AL builds gross income FROM
  SCRATCH (no federal-AGI start; wages from AL Sch W-2). THE QUIRK = federal income tax deduction (L12)
  = (1040 L22 + NIIT 8960 L17) âˆ’ refundable credits (EIC/ACTC/AOC/refundable adoption/2439), floored 0,
  apportioned AL-AGI/federal-AGI for part-year. 2/4/5% rate; sliding-scale std deduction + dependent
  exemption ($1000/$500/$300); Â§414(j)/SS/govt-pension fully excluded (no age-65 exclusion).
- **Source brief** `al_form40_source_brief.md` + **scope walk** (4 AskUserQuestion, all recommended):
  A Form 40 (full + part-year) only, 40NR RED-defer; B COMPUTE the full FIT worksheet + PY apportionment;
  C compute the AGI-keyed sliding scales; D direct-entry Schedule OC, RED-defer ATP/40NR/NOL.
- **Authored `load_al_form40.py`** (SC1040/GA-500 pattern). **Review walk (W1-W5):** all handleable
  (no blocking figure) â€” W1 std-ded encoded as a FORMULA (sidesteps the OCR-suspect MFJ cell, verified
  at several AGI points); W2 rate via Â§40-18-5 + tax-table-confirmed; W3 FIT worksheet basis (Â§40-18-15
  cited); W4 federal handoff; W5 OC caps / 40NR deferred. Ken: "seed + export now" â†’ flipped guard.
- **SEEDED + EXPORTED:** prod **90 â†’ 91 TaxForms** (+AL_FORM_40, draft); `lookup/AL_FORM_40/export/` =
  **HTTP 200** (verified live). 22 facts / 9 rules / 20 lines / 6 diag / 5 tests / 4 flow assertions;
  4 cited AL DOR sources. Commits 1fe6955 (author) + 807af4f (seed/export). Next state form: NC D-400.

## 2026-07-04 â€” SC1040 + Schedule NR AUTHORED + SEEDED + EXPORTED (August state track, form 1)
*Ken: "august." First August RS state item ("SC1040 â€” CC drafts, Ken walks â€” GA-500 pattern").
2nd state individual spec (GA-500 is the precedent). Clear of the parallel S3/S4 federal work.*
- **Two research passes (subagents, verbatim from FINAL 2025 SC DOR PDFs):** (1) SC1040 line map +
  the TY2025 rate (6%, down from 6.4%; 3 brackets 0/3/6% at $3,560/$17,830; $642 rate-sched constant),
  additions/subtractions, credits, dependent exemption $4,930; (2) Schedule NR (Col A/B, line-45
  proration, L48â†’SC1040 L5) + SC depreciation conformity (IRC through 12/31/2024 per Act 63/S.507;
  SC did NOT adopt OBBBA; Â§168(k) bonus add-back line e / line v verbatim; Â§179 conforms at pre-OBBBA).
- **Source brief** `sc1040_source_brief.md` + **scope walk** (4 AskUserQuestion, MAXIMAL, DECISIONS
  D-6): A full resident + Schedule NR; B COMPUTE the Â§168(k) add-back (Ken's depreciation-CPA call,
  diverges from GA-500 direct-entry); C compute the retirement/military/age-65 stack; D RED-defer
  I-335/SC4972/catastrophe, direct-entry SC1040TC.
- **Authored `load_sc1040.py`** (GA-500 pattern; READY_TO_SEED guard). **Review walk (W1-W5):** W1
  Â§179 â€” Ken chose COMPUTE + confirmed the pre-OBBBA figures **$1,250,000 / $3,130,000** (Rev. Proc.
  2024-40; SC's 12/31/2024 conformity) â†’ added R-SC-179-ADDBACK (phaseout-aware excess â†’ line e);
  W2-W5 blessed as in-spec re-verify flags. Flipped READY_TO_SEED=True.
- **Caught a Postgres-only bug:** AuthorityTopic.topic_name >255 (SQLite didn't enforce; the atomic
  txn rolled back clean). Shortened â†’ re-seeded.
- **SEEDED + EXPORTED:** prod **88 â†’ 90 TaxForms** (+SC1040 +SC_SCHEDULE_NR, draft status); both
  `lookup/{SC1040,SC_SCHEDULE_NR}/export/` = **HTTP 200** (verified live). SC1040: 32 facts / 15 rules
  / 27 lines / 6 diag / 8 tests; Sch NR: 5/4/9/1/2; 5 flow assertions; 6 cited SC DOR sources.
  Commits a588cc8 (author) + 2fdbc06 (W1 + seed/export). Next August state form: AL Form 40.

## 2026-07-04 â€” draftâ†’approved workflow: source-controlled approval + first batch (1065-core 7)
*Ken: "the next item, but there's a parallel session so let's not step on it." Next July item =
"begin draftâ†’approved workflow." Stayed clear of the parallel S3/S4 loader work (8835/8936/4835);
used explicit-path commits, not `git add -A` (the 8835-sweep lesson).*
- **State found:** `TaxForm.status` (draft/review/approved/archived) already exists + surfaces in
  serializers/views/export/admin; loaders leave the default â†’ **all 88 forms `draft`** (never exercised).
  No model/migration change (zero collision risk).
- **Design (DECISIONS D-5):** approval is **source-controlled**, reproducible â€” NOT a DB edit (that
  vanishes on `seed_all` rebuild = the "lives only in Supabase" anti-pattern the recon check cleaned up).
  Built `specs/approved_specs.py` (`APPROVED_FORMS` manifest) + `approve_specs` command (draft/reviewâ†’
  approved; reports drift both ways) + wired as **`seed_all` phase 5**. (commit `00e6432`)
- **First batch (Ken: "1065-core batch (7)"):** approved 1065_PAGE1, SCH_K_1065, SCHEDULE_K1_1065,
  1065_M1, 1065_M2, 1065_L, 1065_B â†’ prod now **7 approved / 81 draft**. Held 1065_SE (case-law
  requires_human_review) + the in-flight S3/S4 forms. **Verified reconstructable:** a fresh `seed_all`
  restores exactly those 7 approvals via phase 5. (commit `4a5508b`)

## 2026-07-04 â€” Form 8835 loader homes for the J2/J3/J4 RED-defers + 2 FAs (the S4 arc; the tts session)
- `load_1040_form_8835.py` AMENDED (amend-by-lookup, `update_or_create` â€” the fa-needs-rs-loader-home
  rule; the 8936 R-8936-TRANSFER precedent). Added the four scope-walk RED-defer diagnostics that the
  tts 8835 unit built this session (Ken's 2026-07-04 J2/J3/J4 rulings + the missing-PIS gap): **D_8835_005**
  mixed 1f/4e routing (whole feed withheld), **D_8835_006** straddle window (facility feed withheld),
  **D_8835_007** passthrough with no PIS date (feed withheld), **D_8835_008** producing facility missing
  its PIS date (excluded). All severity=error, â‰¤20 chars, bridge-gated in tts on `form_8835_state`; escape
  hatch = the Form 3800 1zz/4z direct entries. Added **FA-1040-8835-05** (the J2/J3/J4 routing gating_check,
  pins the rulings) + **FA-1040-8835-06** (the constants_check â€” 2025 rate tiers / OBBBA cutoff / Ã—5 / 10% /
  15% bond cap / 90% EPE / 4-yr window; 2026 NOT pinned). Both transcribed verbatim from the tts gate file
  (the canonical set per Ken's 2026-07-01 "tts file stays canonical" ruling).
- SEEDED to RS Supabase: 8835 now 9 diagnostics (was 5) + 6 flow assertions (was 4); all rules keep authority
  links. DB totals: FlowAssertions 422, FormDiagnostics 533.
- â³ Cached tts `server/specs/8835_spec.json` refresh + deployed-export id-level verify FOLLOW the RS Render
  redeploy (this push). tts gate file (`flow_assertions_1040.json`, FA-1040-8835-01..06) is canonical and
  already green (flow gate 397). No id drift expected â€” the loader block is a verbatim transcription.

---

## 2026-07-04 â€” RS DB reconstructability check + `seed_all` orchestrator
*Ken picked this July checklist item after the 1065-core close. "fresh DB + all loaders + diff vs
production; if anything lives only in Supabase â†’ fix now."*
- **Method:** throwaway SQLite DB (`DATABASE_URL=sqlite://â€¦`, guarded), ran every loader, diffed the
  rebuilt DB vs production Supabase on form set + per-form rule_ids + all 11 entity-model counts.
- **Found â€” deploy pipeline gap:** `build.sh` runs only `seed_sources` (feeds + topics). The 89 forms,
  299 authority sources, and 420 flow assertions are ALL seeded by loaders deployment never runs â†’ prod
  was populated by running loaders manually, never verified rebuildable. There was **no orchestrator**.
- **Fixed (code, zero prod risk):** `specs/management/commands/seed_all.py` â€” sources â†’ specs `load_*`
  â†’ amends â†’ flow assertions, dynamic loader discovery + explicit amends list. Fresh-DB run = **61/61
  loaders, 0 problems**. `--dry-run` prints the plan. Closes the one hard break: `load_1040_form_3800`
  is an amend loader that raised `CommandError` when run (alphabetically) before its 1120-S base 3800
  existed; amends-last â†’ 3800 rebuilds to the full 12 rules.
- **4 residual drifts â€” logged for Ken (all prod-data changes, NOT touched this session):**
  (A) orphaned legacy rules no loader reproduces â€” `4797` R001-R008/R010, `SCH_K_1120S` R010-R018,
  `SCHD_1120S` R010-R012 (loaders refactored to new rule_ids; prod never cleaned); (B) prod stale vs
  loaders â€” `8283`/`8949`/`8995`/`8995A` (re-seed, additive); (C) `1065` empty stub (entity=[], 0 rules,
  mislabeled "1065_SE") lives only in DB; (D) `FORM_8582` vs the loader's bare `8582`. **Authority
  sources reproduce EXACTLY (0 delta).** Full writeup + remediation order â†’ `reconstructability_check.md`.
- **Supersession investigation (Ken chose "investigate orphans first", read-only content diff):**
  `4797` orphans R001-R010 = SUPERSEDED (pre-refactor naive rules; R007 hardcodes Â§1250 recap = 0, the
  exact bug the nuance leg fixed) â†’ safe to delete. But `SCH_K_1120S` R010-R018 + `SCHD_1120S` R010-R012
  = **NOT superseded** â€” they encode line-level detail (interest, dividends, meals, distributions, K18
  reconciliation) the current 1120-S loader DROPPED â†’ a loader regression; **do NOT delete, fold into
  the August 1120-S delta audit.** Recorded in `reconstructability_check.md` Â§A + STATUS Known-issues.
- **Prod remediation executed (Ken: "do all safe items"), snapshot-backed + transactional:** deleted
  the 9 confirmed-superseded `4797` orphan rules (+13 cascaded authority links) and the `1065` empty stub
  (+2 cascaded FormLines) â†’ prod **89 â†’ 88 TaxForms**, 420 FA intact; 4797 + 1065 now 0-delta vs the
  rebuild, **authority sources 0-delta**. **CAUGHT MY OWN MISDIAGNOSIS:** an initial `FORM_8582`â†’`8582`
  rename was executed, then the re-diff showed the rebuild produces BOTH `FORM_8582` (the real passive-loss
  form, 12 rules, referenced by 4835) AND a spurious bare `8582` from `load_1120s_complete` â€” so I
  **reverted** the rename immediately (FORM_8582 restored, 12 rules). Investigation also found the four
  "stale" forms EXACTLY match their 1040 primary loaders â€” the extra rules come from `load_1120s_complete/
  specs`, so item B is 1120-S-loader-entangled too. **All residual drift now traces to the 1120-S loader
  family â†’ deferred to the August 1120-S delta audit** (stale rule sets, SCH_K/SCHD orphans + dropped line
  detail, spurious bare-8582 duplicate). No fresh authoring; report/STATUS corrected. `seed_all` + report
  committed; the prod deletes are live in Supabase.

## 2026-07-04 â€” 1065 core campaign CLOSED: forms 5 & 6 (8825/4562/3800) coverage confirmed
*Ken: "check the status and continue." STATUS's IMMEDIATE NEXT was: confirm 8825/4562/3800 cover 1065
(likely no fresh authoring). Verified against the LIVE RS DB â€” not just the brief table.*
- **Entity coverage (live DB query):** `3800` = `['1120S','1065','1120','1040']`, `4562` =
  `['1120S','1065','1120','1040']`, `8825` = `['1120S','1065']` â€” all three carry `1065`.
- **Routing wiring confirmed (not just tags):** `4562` R004 "Â§179 flows to Schedule K (not Page 1)"
  (the 1065/1120S Â§179 pass-through) + R014 line-12 Â§179; `8825` R003 "Total net rental â†’ K Line 2"
  (the exact 1065 Sch K line 2 handoff); `3800` = 12 rules, entity-agnostic GBC aggregation driven by
  the entity tag. So forms 5 & 6 are genuinely wired for 1065, not merely tagged.
- **Verdict: no fresh authoring.** The 1065-core campaign is COMPLETE â€” 6/6 forms covered (4 fresh-
  authored this week: spine `1065_PAGE1`+`SCH_K_1065`, K-1 `SCHEDULE_K1_1065`, M-1/M-2 `1065_M1`/`1065_M2`,
  L/B `1065_L`/`1065_B`; + 3 pre-existing multi-entity 8825/4562/3800). RS side CLOSED. No DB change this
  session (verification only) â†’ still **89 TaxForms / 420 FlowAssertions**.
- **Still open (tts-side, NOT RS blockers):** (1) page-1 off-by-one field numbering (tts internal
  deductions="21"/ordinary="22" vs face 22/23); (2) 1065 Analysis-of-Net-Income build-gap (`R-SCHK-ANALYSIS`
  new; ties M-1 line 9 / M-2 line 3 â€” tts `task_4bf72675`); (3) item-L capital roll-forward (M-2 line 1);
  (4) the 5 Sch L/B build-gaps logged in `1065_core_reconcile_log.md`; (5) optional box-9c DB stamp
  (`test_4797_pipeline_leg.py`). All drive tts-side from the exports.

## 2026-07-04 â€” 1065 core form 4: Schedule L + Schedule B authored + SEEDED + EXPORTED
*Ken: "continue the 1065-core campaign â€” form 4 (Schedule L + Schedule B)." Fresh-authored per D-1.*
- **Sourced verbatim** off the FINAL 2025 f1065.pdf (re-downloaded; page 6 = Schedule L, pages 2-4 =
  Schedule B's 33 questions; pymupdf) â€” confirmed the brief Â§4.3/Â§4.1 transcription. Primary IRC fetched
  verbatim off Cornell LII: Â§754 (Q10 election), Â§448(c) (the $25M base â†’ $31M inflation-adjusted behind
  Q24 Â§163(j)), Â§6221(b) (Q33 audit election out); Â§705 re-used (L21â†”M-2 tax-basis tie).
- **D-1 reconcile** (Explore agent, read-only tts survey): `compute.py` Sch L totals (~L313-329) +
  `compute_schedule_l()` (DepreciationAsset EOY roll-forward) + `seed_1065.py` B1-B18. **9 items logged**
  (`1065_core_reconcile_log.md` L/B section): 2 MATCH (L-totals arithmetic; tts's 9b/12b EOY roll-forward
  is AHEAD), **5 tts build-gaps caught** â€” (L3) no balance check; (B1) Q4 gate stored-but-not-enforced;
  (B2) no $31M/M-3 threshold; (L4) L21â†”M-2 unreconciled; (L2/B3) **tts Sch L numbered L1-L24 offset one
  from the 2025 face** (splits 7a/7b, 19a/19b) + **tts Sch B condensed to 18 questions vs the face's 33**.
- **Scope walk (AskUserQuestion, 4 calls, all approved):** D = author RS to the 2025 face (log the tts
  L1-L24 remap as a build item); **E = Â§754/Â§743(b)/Â§734(b) basis-adjustment MATH RED-defer** (structure +
  cited authority + flag only; Ken's basis-specialty call); F = Schedule M-3 + B-1/B-2/B-3 RED-defer
  (threshold flag + attachment triggers); G = full a/b Sch L sub-lines. â†’ "flip seed export."
- **Authored `load_1065_l_b.py`** (READY_TO_SEED=False â†’ flipped True post-walk): `1065_L` (59 facts / 6
  rules R-L-14/22/BALANCE/21-TIE/EXEMPT/M3 / 28 lines / 5 diag / 5 scenarios) + `1065_B` (51 facts / 5
  rules R-B4-SMALL/B24-8990/B10-754/B33-PR/B30-DIGITAL / 32 lines / 5 diag / 5 scenarios) + 4 flow
  assertions (GATE-SMALL-PTNR-B, RECON-L-BALANCE, RECON-L21-M2, GATE-8990-163J). All rules cited. 6
  authority sources (IRC_705/754/448C/6221 + F1065/I1065 face). Load-bearing computed gates: R-B4-SMALL
  (Q4 all-four â†’ `m_schb_q4_small` suppresses L/M-1/M-2/item F/K-1 item L) + R-B24-8990 (Q24 Â§163(j) $31M).
- **Seeded + exported:** â†’ **89 TaxForms / 420 FlowAssertions**; both `lookup/{1065_L,1065_B}/export/`
  = HTTP 200 (verified live on 127.0.0.1:8137); exports/form_1065_l/ (48 KB) + form_1065_b/ (51 KB),
  all load-bearing rules + verbatim excerpts present. The 6 fresh 1065-core forms are DONE; 8825/4562/3800
  already cover 1065 â†’ campaign near-complete.

## 2026-07-04 â€” Form 3800 1040-side AMENDMENT authored + SEEDED (the S4 arc; the tts session)
*Ken: "should you go ahead and build the 3800?" â†’ spec-first. The deployed 3800 spec was the
1120-S-era draft (10-line generic sketch, K-1-box-13 routing â€” unusable for the 1040/S4 build).*
- **Scope walk (AskUserQuestion, 4 rulings LOCKED, all recommended):** J1 Part III rows = built
  feeders (1f/4e 8835 Â· 1s 8911 Â· 1y/1aa 8936) + 1zz/4z catch-alls; J2 passive = per-inflow
  nullable assertion (None â†’ EXCLUDED + D_3800_002 RED; True â†’ col (d) + D_3800_003 RED with the
  line-3/33 escape hatches â€” 8582-CR manual); J3 carryforward = two direct-entry in-buckets
  (line 4 regular / line 34 specified) + computed CF-out (D_3800_005 + statement; the Part IV
  FIFO grid deferred to the proforma track); J4 Â§6417/Â§6418 OUT (D_3800_004 RED).
- **Review walk (W1-W4 approved):** W1 the stale-grid replacement (deleted 1a/1b/1c, overwrote
  2-7/38 with the 2025 face; entity rules R001-R003 KEPT, R004 refreshed in place); W2
  unanswered-passive-excludes; W3 the line-10b list (= the Form 8911 line-6b Ken-approved
  ordering reading, i3800 verbatim); W4 the S4 all-carries outcome (the 8936 personal credit
  absorbs the ~$2,193 tax first via 10b â†’ line 11 = 0 â†’ the ENTIRE $13,200 specified 8835
  credit carries forward, Sch 3 6a blank â€” F3800-S4 pins it).
- **Authored `load_1040_form_3800.py`** â€” AMEND-BY-LOOKUP (never creates; preserves
  entity_types ["1120S","1065","1120","1040"]): +13 facts / +8 rules (R-3800-P3-INFLOW/
  P3-TOTALS/P1/P2-TAXLIM/P2-SECB/P2-SECC/ALLOWED/CF-OUT) / 42 face lines (Part III P3-prefixed;
  P3-4e is the S4 row) / +6 diagnostics (D_3800_001-006) / +6 tests (F3800-S4 + T2-T6 incl. the
  T3-vs-T4 Â§38(c)(4)(A) TMT-zeroing pair) / +5 FAs (FA-1040-3800-01..05). Authority: NEW
  IRS_2025_3800_FORM (9-page 2025 face, sha256 cdfb169aâ€¦, verbatim Part I/II/III excerpts);
  NEW excerpts on the EXISTING IRS_2025_3800_INSTR (the 10b list; carryover ordering) + IRC_38
  (Â§38(c)(4)(A)-(B) verbatim incl. clause (iv)'s 4-year Â§45 window â€” fetched off LII).
- **Seeded + verified:** loader run (3 stale lines deleted; totals: forms 84 / rules 726 /
  FAs 409; all 3800 rules cited); deployed export re-fetched 200 â€” entity_types preserved,
  rules R001-R004 + R-3800-* both present, stale lines gone, line 38 dest SCH_3.6a. Canonical
  `3800_spec.json` cached in tts.
- **Also this session (tts-side):** the FA-1040-8936-01..05 id collision found + fixed â€” my tts
  gate entries had reused the ids this repo's `load_1040_form_8936.py` had already authored and
  seeded; the tts gate file now carries the RS-canonical five verbatim (extras folded into the
  runners; 5/5 green). NEXT: the tts 3800 unit build (retires D_8911_004, softens D_8936_003),
  then 8835, then the S4 scenario.

---

## 2026-07-04 â€” 1065 core form 3: Schedule M-1 + M-2 (1065_M1 / 1065_M2) SEEDED + EXPORTED
*Ken: "parallel session is working on 3800, you can start on something different" â†’ form 3; walk (M2_3 + seed).*
- **Authored** `load_1065_m1_m2.py` (two forms) from the FINAL 2025 **f1065 page 6** â€” downloaded f1065.pdf
  (334 KB) + extracted pp. 5-6 via pymupdf (verbatim M-1/M-2 line maps; page-6 also has Schedule L for form
  4). M-1: 5 = Î£(1-4), 8 = Î£(6-7), **9 = 5âˆ’8 = Analysis of Net Income line 1** (face literally labels it so â€”
  validates the spine's R-SCHK-ANALYSIS). M-2 (tax basis, Â§705): 5 = Î£(1-4), 8 = Î£(6-7), 9 = 5âˆ’8; line 3 =
  Analysis line 1 = M-1 line 9. Primary IRC Â§705(a)/Â§702 reused verbatim; f1065 p.6 + i1065 as filing
  authority. All rules cited.
- **Reconcile vs tts `FORMULAS_1065` M-1/M-2 (5 findings):** (1) ðŸ”´ **M2_3 mis-source** â€” tts labels line 3
  "Net income (loss) per books" + free data-entry (`compute.py` M2_5 sums it raw); the FINAL face line 3 =
  "(see instructions)" = Analysis line 1 on the post-2020 **tax-basis** M-2. Ken: **"log + spawn a tts task"**
  â†’ `spawn_task` `task_4bf72675` (coupled to the unbuilt 1065 Analysis compute + M-1 line 9; the RS spec
  stays correct per current law). (2) M1_9 ties to Analysis line 1 which tts doesn't compute (spine gap #6).
  (3) M2_1 = Î£ K-1 item-L begin capital but item-L roll-forward is RED-deferred (K-1 leg) â†’ data-entry.
  (4) tts adds catch-all M1_4c/M1_7b not on the face (benign). (5) Sch B Q4 small-partnership exemption â†’
  gating fact (shared with L/K-1 item L).
- **Seed + export:** hit a varchar(20) cap on a flow-assertion id (`GATE-SMALL-PARTNERSHIP` = 22 chars â†’
  atomic rollback, no partial seed) â†’ renamed `GATE-SMALL-PTNR`, re-seeded clean. 1065_M1 (5 rules / 11
  facts / 10 lines / 2 diag / 3 scenarios) + 1065_M2 (6 rules / 12 facts / 11 lines / 3 diag / 3 scenarios)
  + 3 flow assertions, all cited â†’ **87 TaxForms / 416 FlowAssertions**. Both `lookup/{1065_M1,1065_M2}/
  export/` = **HTTP 200** (exports/form_1065_m1/ + form_1065_m2/, ~32 KB each). Committed `0184c0a` (author)
  + this seed. **Form 3 of 6 DONE. Next: form 4 â€” Schedule L + Schedule B.**

---

## 2026-07-04 â€” 1065 core form 2: Schedule K-1 + allocation engine (SCHEDULE_K1_1065) SEEDED + EXPORTED
*Ken: "start it" â†’ author form 2; walk (coded-box depth + flip); "full ~200-code transcription now" + "flip seed export".*
- **Reconcile-driven authoring.** Explore agent mapped tts `k1_allocator.py` + `compute_schedule_k1.py`
  read-only. Encoded: per-partner box = entity Sch K line Ã— `profit_pct` (â‰¥0) / `loss_pct` (<0), overridable
  per-category by `PartnerAllocation` (Lacerte special allocations); GP (4a/b/c) + distributions (19a) DIRECT
  per-partner; box 9c = LT_CAPITAL/`profit_pct` (reads K9c â†’ writes box 9c) â€” **CONFIRMED, closes the box-9c
  pass-through** (RECON-9C: 80k @ 60/40 â†’ 48k/32k); box 14a = the `1065_SE` spec (cross-ref).
- **RED-deferred (Decision C; engine absent):** Â§704(c) built-in gain (items M/N â†’ D_K1_704C), Â§704(b) SEE
  (D_K1_SPECIAL_ALLOC), Â§706(d) varying interest (D_K1_706D), item-L capital roll-forward (D_K1_ITEML â€” tts
  stores the fields but doesn't compute; **M-2 line 1 can't auto-derive** â†’ M-2 leg). Gap logged: `capital_pct`
  defined but UNUSED by the allocator (D_K1_CAPPCT).
- **Authority:** primary IRC verbatim â€” Â§704(a)/(b), Â§706(d)(1), Â§752(a)/(b), Â§705(a) (Cornell LII this
  session); Â§702(b)/Â§707(c) reused. **FULL coded-box transcription (Ken decision):** downloaded the FINAL
  i1065sk1.pdf (445 KB, 36 pp), extracted pp. 33-36 "List of Codes" via pymupdf â†’ boxes 11/13/14/15/17/18/19/20
  (every letter A-ZZ) encoded VERBATIM as 8 `IRS_2025_I1065SK1` AuthorityExcerpts (source-grounded, not
  recalled; they ride into the export). WebFetch mangles dense code tables â†’ direct PDF extraction.
- **Seed + export:** READY_TO_SEED=True â†’ SCHEDULE_K1_1065 (27 facts / 11 rules / 19 auth links / 17 lines /
  7 diag / 8 scenarios / 4 flow assertions, all cited) â†’ 85 TaxForms. `lookup/SCHEDULE_K1_1065/export/` =
  **HTTP 200**, exports/form_schedule_k1_1065/ (80 KB; 8 code-list excerpts present). Committed `8673fdd`
  (author) + this seed. **Form 2 of 6 DONE. Next: form 3 â€” Schedule M-1 / M-2.**

---

## 2026-07-04 â€” 1065 core campaign KICKOFF: Schedule K spine SEEDED + EXPORTED (+ a tts bug fixed)
*Ken: "go" â†’ author the first of 6 forms; walk (D-1); "dig into net-farm" â†’ "fix now"; "flip seed export".*
- **SEED + EXPORT (Ken: "flip seed export"):** flipped `READY_TO_SEED=True`, ran `load_1065_schedule_k`
  â†’ `1065_PAGE1` (27 facts / 7 rules / 32 lines / 3 diag / 4 scenarios) + `SCH_K_1065` (40 / 11 / 38 / 4 /
  7 + 4 flow assertions), all rules cited â†’ RS **84 TaxForms / 404 FlowAssertions**. Exported via the real
  `form_lookup_export` view (APIRequestFactory): both `lookup/{1065_PAGE1,SCH_K_1065}/export/` = **HTTP 200**,
  saved to `exports/form_1065_page1/` + `exports/form_sch_k_1065/` (51 KB / 70 KB; line_map 32 / 38). Spine
  leg (form 1 of 6) DONE. **Next: form 2 â€” Schedule K-1 (Form 1065) + the allocation engine** (reconcile
  `k1_allocator` Â§704 math + `compute_schedule_k1` box map; transcribe the ~200 coded-box lists; close the
  box-9c pass-through).
- **Scope walk (AskUserQuestion, 3 decisions LOCKED):** A. K-2/K-3 international â†’ **RED-defer** (box 16 =
  Schedule K-3-attached checkbox only + `D_SCHK_K3`); B. Schedule M-3 â†’ **RED-defer** (belongs to the L/M
  leg; threshold gating fact there); C. Â§704(b)/(c) â†’ **encode structure, defer math** (items J/K/L/M/N +
  %-alloc as facts + cited Â§704 authority + gating flags; special-allocation MATH deferred to tts
  `k1_allocator`; `D_SCHK_704C` surfaces item M/N). All three on the recommended calls.
- **Authored `specs/management/commands/load_1065_schedule_k.py`** (fresh, per D-1) â€” seeds TWO forms
  mirroring the 1120-S decomposition (`1120S_PAGE1` + `SCH_K_1120S`):
  - **`1065_PAGE1`** â€” Form 1065 page 1: income 1a-8 (1c=1aâˆ’1b; 3=1câˆ’2 COGSâ†1125-A; 8=Î£3-7; L5â†Sch F;
    L6â†4797 PtII L17), deductions 9-22 (16c=16aâˆ’16bâ†4562; 22=Î£9-21), **ordinary business income
    line 23 = 8âˆ’22 â†’ Sch K line 1** (the handoff, `R-1065P1-23`). 27 facts / 7 rules / 32 lines /
    3 diagnostics / 4 scenarios. âš  2025 face: ordinary income is L23 (NOT 22).
  - **`SCH_K_1065`** â€” Schedule K distributive-share spine (Total-amount col) lines 1-21 + Analysis of
    Net Income line 1 = (Î£ 1-11)âˆ’(Î£ 12-13e+21). Line 1â†page-1 L23; 3c=3aâˆ’3b; 4c=4a+4b; 9câ†4797;
    14a=the `1065_SE` spec (cross-ref, not recomputed); line 16=K-3 checkbox (RED-defer). ~30 facts /
    11 rules / ~40 lines / 4 diagnostics / 7 scenarios. Kâ†’K-1 box map (`R-SCHK-KMAP`) + Â§704 allocation
    structure (`R-SCHK-ALLOC`) authored as routing rules (per-partner math = the K-1 leg).
  - Authority: **primary IRC quoted VERBATIM** â€” Â§702(a)/(a)(8)/(b), Â§703(a)/(b), Â§704(a)/(b) (fetched
    2026-07-04 off Cornell LII this session), Â§707(c) (reused from the vetted 1065_SE load); + FINAL-2025
    **f1065/i1065** line maps as filing authority (`IRS_2025_F1065`/`IRS_2025_I1065`, requires_human_review,
    from the brief Â§4.1/Â§4.2 verbatim transcription). 4 flow assertions (RECON-P1-K1, RECON-ANALYSIS,
    INV-K-CHARACTER, GATE-K2K3-DEFER). All rules cited.
- **Validation:** `py_compile` OK; the READY_TO_SEED=False refuse-to-seed guard fires clean ("all
  populated" â€” nothing hollow, held only on the sentinel). NOT seeded (awaits the walk per D-1).
- **D-1 reconcile survey** (read-only, tts `server/apps/returns/compute.py` entity Sch K block ~L240-298
  + `compute_schedule_k1.py`) â†’ **`1065_core_reconcile_log.md`, 8 items:**
  - âœ… MATCH Ã—4 â€” page-1 L8=Î£(3-7) (`:240`); K3c=K3aâˆ’K3b (`:284`); K14a bottom-up SE (`:288-292`,
    reconciled this season); Â§179â†’K12 for 1065 (`:984`).
  - ðŸ”¨ BUILD-GAP Ã—1 â€” tts has **no 1065 Analysis of Net Income** compute (`K18` at `:120` is 1120-S income
    reconciliation only); `R-SCHK-ANALYSIS` is new â†’ a tts build item (ties to M-1 L9 / M-2 L3, L/M leg).
  - âš  KEN ADJUDICATION Ã—3 â€” (a) page-1 **off-by-one field numbering**: tts internal deductions=field"21"
    (Î£9-20), ordinary=field"22"(8âˆ’21), K1â†"22" vs the 2025 face 22/23 (arithmetic identical; map or
    renumber); (b) **net-farm routing** â€” tts routes Sch F net (F34)â†’**Sch K line 11** (`:287`), but the
    face puts net farm on **page-1 line 5**â†’ord incomeâ†’K1 â€” Ken's farm/depreciation call (check
    double-count); (c) **box-9c pass-through** = the STILL-OPEN tts verification (STATUS Next-up).
- **Files:** `load_1065_schedule_k.py` (new), `1065_core_reconcile_log.md` (new), STATUS.md updated.
  Committed `bbe6913`; loader inert (READY_TO_SEED=False) until the walk.
- **ðŸ› CONFIRMED + FIXED a tts bug the reconcile caught (net-farm misroute).** Ken: "dig into the tts
  net-farm path to confirm double-count" â†’ then "fix now in tts + add test." Traced via an Explore agent
  (which I corrected on one point â€” it claimed `F34=0` for 1065, conflating the inline `F34=F9âˆ’F33` formula
  in `FORMULAS_1065:278` with the 1040-only `compute_schedule_f_family`; verified `seed_1065` seeds the full
  enterable F-block, so `F34` IS computed inline). **Bug:** `FORMULAS_1065` routed `F34` â†’ **Schedule K line
  11** (`compute.py:287`) instead of page-1 line 5 â†’ K1. Two modes: (a) F-block only â†’ farm on K11 not K1 â†’
  the 14a SE base (reads K1 only) omits it â†’ **SE understatement**; (b) F-block + hand-entered line 5 â†’
  **double-count**. **Fix (tts `f61cfec`):** relocated the Schedule F block ahead of page-1 line 8; added
  `("5", F34)` so farm flows line 5 â†’ 8 â†’ 22 â†’ **K1** (and the SE base); removed `K11â†F34`; `seed_1065` line 5
  `is_computed=True` (YELLOW). Pure-Python sim confirmed routing; `TestNetFarmRouting` (3 tests) **3/3 green**
  over the shared test DB (one AdminShutdown blip re-ran clean, per `tts-test-db-collisions`). **Committed
  INDEX-ONLY** â€” the parallel S3/S4 session has heavy uncommitted 8936 work in the same `compute.py` (+ models/
  views/serializers/migrations); staged only my FORMULAS_1065 hunks via a filtered patch (`git apply --cached`)
  + the 2 mine-only files, leaving their WIP untouched. Pushed clean (`962be0a..f61cfec`, fast-forward).

---

## 2026-07-04 â€” Between-session prep: S3/S4 integrity checker + 1065-core source brief (pre-scout for the July campaign)
*Independent RS work while the parallel tts session builds S3/S4 â€” zero collision.*
- **`check_s3s4_integrity.py`** (committed `a73d424`): pre-seed math+structure gate for 4835/8835/8936/
  8936_SCHA â€” independent re-derivation of every test-vector's arithmetic (constants re-typed, not
  imported) + id<=20 / all-cited / fact-key-input / no-dupe gates + constants cross-check. **390 checks,
  all green.** Also verified the DEPLOYED Render endpoints match the local seed exactly (4835/8835/8936/
  8936_SCHA â€” rules/facts/line_map counts identical; the tts consuming contract is live, not just local).
- **`1065_core_source_brief.md`** (this commit): pre-scouted the NEXT campaign (July 1065 core). Gap map
  (6 forms to author fresh â€” Sch K, K-1+allocation, M-1/M-2, L, B; 8825/4562/3800 already cover 1065),
  the D-1 reconcile targets in tts (`k1_allocator.py` / `compute_schedule_k1.py` / `compute_1065_se.py`,
  read-only survey), and **Â§4 verbatim FINAL-2025 line maps** (3 research agents read f1065/f1065sk1/
  i1065/i1065sk1 directly): page-1 (ord. income = line 23; tax/pmt 24-32; new direct-deposit 32b-d) +
  Schedule B (33 Qs; Q4 L/M exemption receipts<$250k & assets<$1M; Q10 Â§754; Q23/24 Â§163(j) $31M) +
  Schedule K (1-21 + Analysis) + K-1 (Part II items J/K/L/M/N, Part III 1-23) + the Kâ†’K-1 coded-box
  mapping + K-2/K-3 split + OBBBA What's New (Â§174A R&E, Â§181 box-13 X, Â§1062 box-20 ZZ). Cross-tie: K-1
  box-15 credit codes AY/AZ/AB carry the 8936/8835 credits I specced this session. NOT authorized to
  seed â€” D-1 fresh-author + Ken walk when the campaign opens.

## 2026-07-04 â€” S3/S4 unblock campaign: 8835 + 8936 + Schedule A(8936) authored/seeded/exported; 4835 reconciled â€” ALL FOUR endpoints 200
*Ken's campaign prompt (from a tts Claude): author the four missing specs so the tax app can build the
last two 1040 MeF ATS scenarios (S3 = 4835; S4 = 8936 + Sch A + 8835). Started from the tts authoring
notes (`server/specs/form_{4835,8936,8835}_authoring_notes.md`) as HYPOTHESIS, verified every rule
against the FINAL 2025 IRS sources (Authoritative-Source Rule).*
- **IRS-source verification (2 parallel subagents, read FINAL 2025 PDFs verbatim):**
  - 8835 (Cat. 14954R, i8835 Cat. 55349M 12/22/25): all Â§45 resources gate on "construction begins
    before 2025" (no per-resource variance); OBBBA touched ONLY advanced-nuclear energy communities
    (TY after 7/4/25) â€” NOT the begin-construction gate; Â§45Y/Â§48E is a DIFFERENT form (D_8835_004).
    2025 rates $0.006/$0.003 (Fed. Reg. 2025-09366); Ã—5 (line 9) + 10%/10% (lines 10/11). line 15 ->
    Form 3800 line 4e (within 4-yr PIS window) or 1f. New 2025: 8c PWA -> Form 7220 (D_8835_003).
  - 8936 (Cat. 37751E; Sch A Cat. 93602W 8/21/25; i8936 Cat. 67912V 10/14/25): **OBBBA "acquired after
    September 30, 2025" termination** (25E/30D/45W), restated 4Ã— in the instructions; "acquired" =
    written binding contract + payment (nominal down payment/trade-in counts). MAGI caps UNCHANGED by
    OBBBA (new 150/225/300k; used 75/112.5/150k), **best-of-2024-or-2025** test. Used = lesser $4,000/
    30%, price <= $25k. Commercial = min(15%/30% basis, incremental), $7,500/$40,000. Personal credits
    NONREFUNDABLE and **LOST if unused** (no carryforward); business/commercial -> Form 3800.
- **4835 reconciled** (`load_1040_form_4835.py`, re-seeded): added the S3 ATS vector (Lynette Heather:
  L1=17,035, expenses 5,974 -> L32=11,061 -> Sch E 40/42, nothing to SE) + the [VERIFY-QBI] item resolved
  (R-4835-QBI/D_4835_QBI: crop-share rent is QBI ONLY if it rises to a Â§162 trade/business / self-rental /
  RP 2019-38 safe harbor â€” default NOT-QBI, preparer-asserted; cited Â§199A). Now 55 facts / 12 rules / 13 tests.
- **`load_1040_form_8835.py`** (`8835`, 7 rules all cited / 32 facts / 38 lines / 5 diags / 5 tests / 4 FA):
  Â§45 credit calc + OBBBA before-2025 gate + Ã—5/+10%/+10% + line-15 4e/1f routing + S4 solar vector
  ($2,640 -> Ã—5 -> $13,200 -> 3800 line 4e). New sources IRS_2025_8835_FORM/INSTR, IRC_45. Year-keyed rate table.
- **`load_1040_form_8936.py`** (TWO forms â€” the Sch F precedent): `8936` (5 rules / 16 facts / 29 lines /
  3 diags / 4 tests) + **`8936_SCHA`** (5 rules / 24 facts / 43 lines / 4 diags / 5 tests / 5 FA). OBBBA
  9/30/2025 per-vehicle gate (D_8936_001, highest precedence); MAGI best-of-two-years; used/commercial
  formulas; routing L8->3800 1y, L13->Sch3 6f, L18->Sch3 6m, L21->3800 1aa, transfer repay new->Sch2 1b/
  used->1c. New sources IRS_2025_8936_FORM/8936SA_FORM/8936_INSTR, IRC_30D_25E_45W.
- **Schedule A (Form 8936) canonical lookup key = `8936_SCHA`** (my call; the 1120S_SCHL convention; the
  key Ken probed). Exposed as a SEPARATE form (own Cat. No. 93602W, Attach. Seq. 69A; per-vehicle) so the
  tts build computes per-vehicle then aggregates to 8936.
- **VERIFIED all four export endpoints return 200** (live server, control 9999 -> 404): 4835, 8835, 8936,
  8936_SCHA. Self-contained exports saved to `exports/form_{4835,8835,8936,8936_scha}/`.
- **Open [VERIFY] carried for the tts build (flagged, not guessed):** the S4 new-vehicle TENTATIVE credit
  is BLANK on the scenario form (seller report) â€” do NOT assume $7,500; the S3/S4 tests pin gates+routing,
  not the disputed dollar. Also: 8936 line-1a "11a"-vs-11 asymmetry; the 6m credit-ordering (line 11 vs 16);
  8835 line-15 4e window for the S4 solar PIS 9/22/2023. All in the loader headers as walk items.
- RS DB: **82 TaxForms / 400 FlowAssertions**. Recorded **D-4** in DECISIONS.md.

## 2026-07-04 â€” FORM_4835 (Farm Rental Income and Expenses) authored, seeded, exported â€” parallel-session 404 CLEARED
*Pivot origin: a parallel tts session's S3 resume pointer needed Form 4835, which had NO RS spec
(GET /api/forms/lookup/4835/export/ 404'd; only an authority stub existed). Ken ruled "start the 4835 spec."*
- **Source-verified** the 2025 Form 4835 face + instructions VERBATIM (f4835.pdf, Cat. No. 13117W, Attach.
  Seq. 37, Created 1/7/26 â€” read pages 1-3 via the Read tool). New source `IRS_2025_4835_FORM`; 11 existing
  sources referenced (IRC_1402A1/469/465/77/451_EF/263A, 6198/8582/Sch-E instr, Pub 225).
- **Ken walked 4 scope decisions (AskUserQuestion):** (1) LOSS PATH â€” compute the full path, not RED-defer
  ("this is for MeF testing ... 8582/6198"); (2) SE-exclusion â€” explicit hard invariant + flow-assertion;
  (3) elections â€” capture-$-flag + material-participation routing diagnostic; (4) multi-instance per-activity.
  Recorded as **D-3** in DECISIONS.md.
- **`load_1040_form_4835.py`** (READY_TO_SEED guard, flipped on Ken's in-session "approve, flip and seed"):
  form `4835` â€” 54 facts / 11 rules (ALL cited) / 52 lines / 8 diagnostics / 12 scenarios / 9 flow assertions.
  Verified L7 gross = right-column sum (1+2b+3b+4a+4c+5b+5d+6). Loss path computes Â§465 at-risk (Form 6198)
  BEFORE Â§469 passive (Form 8582; $25k active-participation special allowance) â†’ line 34c â†’ Sch E line 40;
  integrates the EXISTING RS 6198 (1120-S loader) + FORM_8582 (Sch E loader) specs, does not re-author them.
  Hand-computed 8582/6198 figures in T3/T4/T5/T6.
- **Flow correction:** the old authority stub said "income â†’ Sch E Part I"; the face is L7 gross â†’ **Sch E
  line 42** (farming/fishing reconciliation), L32 net / L34c loss â†’ **Sch E line 40**. Corrected the stub
  excerpt in `sources/federal_data/forms_supporting.py`.
- **form_number gotcha:** first seeded as `FORM_4835`, but the lookup is `form_number__iexact` with NO
  `FORM_` normalization and the tts pointer requests bare `4835` (matches the 8829/6251/8283 convention) â€”
  renamed to `4835`, deleted the orphaned row (161 objs cascade + 8 links), re-seeded clean.
- **VERIFIED the 404 is cleared:** `GET /api/forms/lookup/4835/` and `/export/` both return **200** (APIClient,
  localhost host). Export = 90 KB self-contained package (11 rules / 54 facts / 52 line_map / 8 diagnostics /
  12 tests / 11 authority sources), saved to `exports/form_4835/form_4835_spec.json`. The parallel tts session
  can now fetch its spec live and resume S3.
- RS DB: TaxForms 79. Walk items A (8582 special-allowance figures), B (4835 â†’ 8582 active-rental-RE bucket),
  C (SE guard covers the farm-optional gross too) noted in the loader header for the tts build leg.

## 2026-07-04 â€” Season checklist RS track + D-2 recorded + status-mirror extended to RS (public repo created)
*Cross-repo housekeeping per Ken's "INSTRUCTION FOR CC" â€” no spec/compute work. Active RS task
(K-1 box 9c pass-through verification) is UNCHANGED and still next-up.*
- **SEASON_CHECKLIST.md (tts-tax-app `fde3655`):** added the `RULE STUDIO AUTHORING TRACK` section
  (Ken rulings D-1/D-2 header; Julyâ†’Octâ€“Nov RS authoring plan â€” 1065 core, state specs, 1041 spine),
  placed before the standing Unplanned-work-log tail. Edited the SOURCE repo only; the public mirror
  is regenerated by the sync script (never hand-edit `tts-tax-status`).
- **DECISIONS.md (RS `48e44cc`):** recorded **D-2 â€” 1041 Schedule I (AMT) RED-DEFERRED for season one**
  (loud RED diagnostic on AMT indicators; no Schedule I compute built; revisit only if regression demand
  warrants). Real dated entry at the top per the append-at-top convention; cross-refs D-1 (1065 core
  specs authored FRESH from IRS primary sources, existing 35 compute formulas reconciled against each
  spec â€” never spec-from-code; every mismatch = logged Ken adjudication). `last_updated` â†’ 2026-07-04.
  The two `<Short decision title>` template stubs left below as format examples (didn't delete).
- **sync_status_mirror.ps1 (tts-tax-app):** extended to also mirror RS `STATUS.md` + `session_log.md`
  into a **`rule-studio/` subfolder** of the public `tts-tax-status` mirror (subfolder avoids colliding
  with tts-tax-app's own `STATUS.md`). PII guard refactored to an `Assert-CleanFile` function and now
  covers the RS files too; both verified clean (0 SSN/EFIN hits). PS 5.1 parse-checked.
- **Created the public GitHub repo `klill6506/tts-tax-status`** â€” it never existed (pushes were 404ing;
  this was the carried "one-time" item in tts STATUS). Public per Ken's explicit call, via the stored
  `klill6506` classic PAT (`repo` scope) â€” no `gh` installed. The local mirror clone `D:\dev\tts-tax-status`
  already existed; set upstream tracking, pushed. Verified the remote now holds the root planning files +
  `rule-studio/STATUS.md` + `rule-studio/session_log.md`; a fresh sync run reports "already current".
- **âš  PRIVACY (new standing constraint):** RS `STATUS.md` + `session_log.md` are now **PUBLICLY mirrored**
  (RS repo itself is going private). Keep client PII and sensitive firm specifics OUT of them â€” the PII
  guard only blocks SSN/EFIN shapes, not prose. Saved to `.claude` auto-memory too.

## 2026-07-03 â€” 8995A amended: Schedule D patron reduction + capped DPAD COMPUTED (Ken ruling â€” MeF ATS S2)
- **Ken RULED (AskUserQuestion): "Is this a MeF test scenario? If so build 8995-A Schedule D"** â€” S2
  (Jones) stipulates ag-co-op patrons who "do not qualify" for QBI; enacted law routes patrons to
  8995-A at ANY income (i8995a 2025 'Who Can Take the Deduction') with the face line-3 skip at/below
  the threshold, and the Â§199A(b)(7) reduction = min(9% Ã— allocable QBI, 50% Ã— allocable W-2 wages)
  is $0 for a zero-wage business â€” the ATS key's blank 13a is scenario fiat, documented divergence.
- **Amended `load_1040_form_8995a.py`** (amend-by-lookup, ids stable): +facts `a_business_schd_qbi_alloc`
  / `a_business_schd_wages_alloc` / `a_dpad_199ag`; R-8995A-PATRON reauthored routingâ†’calculation
  (SD2â€“SD6 chain â†’ L14); R-8995A-SCOPE/P2-COMP/P4-LIMIT amended (patron-at-any-income, L15 floor,
  L38 cap = L33 âˆ’ L37 face verbatim); +7 SD line-map rows; D_8995A_001/002 REPURPOSED errorâ†’info
  (**Ken ruled info**: patron-no-alloc confirm-the-zero; DPAD clipped) + NEW D_8995A_008/009 guards;
  T9 amended + T11â€“T15 hand-computed (T13 = the S2 below-threshold zero-wage patron, LOAD-BEARING);
  FA-1040-8995A-08 gating_check â†’ formula_check. New authority source IRS_8995A_SCHD_FORM
  (f8995ad Rev 12-2022 verbatim) + patron-rules excerpt on IRS_2025_8995A_INSTR.
- **`check_8995a_integrity.py` extended** (own Sch D/skip/cap transcription) â€” ALL CHECKS PASS,
  15 scenarios re-derived.
- **Seeded RS Supabase** â†’ deployed export drift = EXACTLY the amendment (24 facts / 11 rules /
  58 lines / 9 diags / 15 tests; old T9 retired) â†’ canonical `8995a_spec.json` refreshed in tts.
- tts build same session (`f10e864`): mig 0158, engine + router + render + FormEditor; the retired
  `D_8995_001` is dormant in rules_schedule_c. Flow gate 381 (FA-08 amended in place).

## 2026-07-03 â€” 1040_EIC amended: `eic_opt_out` (1040 line 27c) â€” Ken ruled ACTC-sibling skip-entirely (S2 prep session)
- **Ken RULED (AskUserQuestion): "Skip-entirely, ACTC-sibling"** for the 2025 Form 1040 line 27c
  election ("If you do not want to claim the EIC, check here" â€” face verbatim, verified against the
  official 2025 f1040 PDF): the election disengages the EIC computation and every D_EIC diagnostic,
  CLEARS line 27a (never compute-then-zero), Schedule EIC does not attach, the 8867 gate stays
  consistent automatically (27a > 0 keying). Needed by ATS Scenario 2 (Jones) â€” their
  statutory-employee Sch C would otherwise hit the D_EIC_015 RED-defer; the scenario declines via 27c.
- **Amended `load_1040_eic.py`** (commit `e64dbea`): +fact `eic_opt_out` (sort 70), R-EIC-27A formula
  gains the opt-out gate (inputs now ["eic_opt_out"]), +D_EIC_017 (info â€” the D_8812_014 sibling
  explaining the blank line), +scenario EIC-G6 (opted-out qualifying return â†’ 27a BLANK, only 017
  fires), +FA-1040-EIC-10 (loader-homed; pins the ruling incl. the stale-27a clear).
- **Seeded RS Supabase** (idempotent; FlowAssertions 381 â†’ 382) â†’ **deployed export verified**
  (fact/diag/scenario/rule-gate all present; drift = exactly the 3 additions) â†’ canonical
  `eic_spec.json` refreshed in tts (tests 16 â†’ 17).
- tts build same session: mig 0156, eic_engaged + compute_eic opt-out gates, D_EIC_017 in rules_eic,
  c2_13 render, DoNotClaimEICInd in the MeF mapper, FA gate 380 â†’ 381, topic7 suite extended.

## 2026-07-03 â€” 4797 NUANCE LEG (the 3 depreciation nuances) authored + gated + SEEDED + EXPORTED (Ken: "go ahead" + 2 decisions)
- Ken: "continue with the three 4797 depreciation nuances" â†’ verified all law verbatim (Cornell LII +
  2025 i4797) BEFORE any code, then walked 2 design decisions (AskUserQuestion):
  - **D1 (nuance 1):** a NEW per-asset classifier field `f4797_section_1245_exception`
    (none / single_purpose_ag / petroleum_storage / railroad_grading) auto-returns Â§1245 for the
    Â§1245(a)(3) real-property exceptions (D)/(E)/(F) + a per-exception info diagnostic
    (`D_4797_1245AG` / `D_4797_1245PETRO` / `D_4797_1245RRGR`). (C) Â§179-realty stays via D_4797_179REAL;
    (G) QPP via is_qpp/D_4797_QPP.
  - **D2 (nuances 2+3):** COMPUTE line 26a = max(0, actual accumulated depr incl. bonus âˆ’ SL on the
    UNREDUCED basis) in the tts engine where the disposed Â§1250 asset has the MACRS data â€” ONE computation
    covering both 150DB land improvements (Â§168(b)(2)(A)) and bonused QIP; preparer-overridable.
    `D_4797_ADDL` demoted to the FALLBACK gate (fires only when the engine can't compute). Applicable % = 100%.
- **Law (verbatim, verified 2026-07-03):** Â§1245(a)(3)(D)/(E)/(F) + the Â§168(i)(13) (livestock enclosure /
  commercial greenhouse) and Â§168(e)(4) (railroad grading) definitions; Â§1250(b)(1)/(b)(3) â€” the (b)(3)
  carve-out is PRE-1976 Â§168 only, so current MACRS + Â§168(k) bonus ARE depreciation adjustments (nuance 3
  now statutorily grounded, not just i4797); Â§168(b)(2)(A) 150DB for 15-yr land improvements; i4797 line 26a
  "do not reduce the basis... to figure straight line". NEW `IRC_168` authority source (4 verbatim excerpts).
- **Authored** into `load_4797.py`: +1 fact (the classifier), R-4797-CHARCLASS + R-4797-ADDLDEPR rewritten
  (updated in place, no new rule ids), +3 info diagnostics, +4 scenarios (N1 agâ†’Â§1245 math; N2-N4 the
  exception diagnostics), +IRC_168 source/links, +the i4797 "unreduced basis" clause. `check_4797_integrity.py`
  extended (N-branch validation). **Gate ALL PASS: 27 facts / 8 rules / 34 lines / 14 diagnostics / 20
  scenarios / 19 rule links / 9 sources.** Committed GATED (`03a5606`).
- Ken: **"Approve â€” seed + export"** â†’ seeded RS Supabase (idempotent; "Updated Form 4797", all rules cited;
  TaxForms 78 / FlowAssertions 381) â†’ exported `4797_spec.json` to tts (facts 27 / diagnostics 14 / tests 21
  [1 pre-existing DB orphan scenario] / sources 14 [all linked]) â†’ verified the new content landed
  (classifier fact, D_4797_1245*, IRC_168, N1-N4).
- **tts build leg â€” COMPLETE (both sub-legs), committed tts `98ac1c5` (A) + `be47294` (B); push HELD, see below.**
  - **SUB-LEG A (nuance 1, classifier):** DepreciationAsset.section_1245_exception
    (none/single_purpose_ag/petroleum_storage/railroad_grading) + migration 0157; resolve_recapture_type
    returns Â§1245 for a set (D)/(E)/(F) exception (after override + is_qpp); 3 info diagnostics
    D_4797_1245AG/PETRO/RRGR; test_4797_spec.py +5 classifier tests, _make_asset mock defaults the field 'none'
    (a bare MagicMock attr reads truthy â†’ would force Â§1245).
  - **SUB-LEG B (nuance 2, engine-computed 26a):** depreciation_engine.calculate_1250_additional_depreciation
    = max(0, accumulated actual incl. bonus âˆ’ SL-equivalent on the UNREDUCED basis), SL summed via
    _macrs_pct("SL",...) over the holding period + disposal proration (Â§179 reduces the SL basis, bonus does
    NOT â€” i4797); returns None when the MACRS data is missing. compute._resolve_1250_additional_depr +
    aggregate_dispositions wiring (preparer non-zero overrides â†’ else engine â†’ else 0). D_4797_ADDL demoted to
    the FALLBACK gate (fires only when the engine can't compute). +5 fast unit tests (hand-verified 10-yr HY
    case: actual 70k âˆ’ SL 50k = 20k; unreduced-basis; zero-floor; None; resolve override/compute/fallback).
  - **VERIFIED: 49 fast unit tests + the pipeline DB stamp 15/15 green** (single-purpose ag â†’ Â§1245; 150DB
    computed-26a end-to-end; preparer override; the D/E/F exception diagnostics; D_4797_ADDL fallback on a
    non-computable asset). One transient pooler DEADLOCK (parallel-session DB contention) re-ran clean; one
    stale D_4797_ADDL assertion was CORRECTLY failing (the demotion) â†’ retargeted.
  - **tts push RESOLVED (2026-07-03):** the parallel EIC session committed its `0156_taxpayer_eic_opt_out`
    (`c53e942`) ON TOP of the two 4797 commits in the shared local repo and pushed the whole chain â€” so
    `98ac1c5` + `be47294` are now on remote main (origin/main == local HEAD, 0 ahead). Migration chain is a
    clean linear 0155â†’0156â†’0157 (both files present; 0157 depends on 0156 â€” Django resolves by the dependency
    graph, not commit order), no merge migration, Render-deploy-safe.
- **DONE â€” the 4797 nuance unit is fully closed across all three nuances:** specâ†’seedâ†’exportâ†’buildâ†’unitâ†’
  DB-verified, all on remote (RS + tts).

---

## 2026-07-03 â€” FORM 8283 authored + SEEDED (ATS Scenario 2's tax-law form; Ken's walk: J6 RULED warn-only)
- Ken: "go" â†’ the S2 (Form 8283) spec-first unit per the smallest-first ruling. OBBBA check at
  the spec leg: Â§170(f)(11)/(f)(12) untouched by P.L. 119-21; Rev. 12-2025 form + instructions
  fetched verbatim (i8283 + USC Â§170(f)(11) via law.cornell.edu).
- **Authored `load_1040_form_8283.py`** (commit `0748f06`): AMENDS the shared "8283" TaxForm BY
  LOOKUP (1120S/1065/1040 entity_types preserved â€” the rs-amend-shared-form lesson); RETIRES the
  load_1120s_complete placeholder stub (10 facts / 5 unnamed rules / SA-*/SB-1 lines / D001-D003 /
  2 tests â€” never approved, never seeded to tts). 51 facts / 5 rules (R-8283-FILE/SECTION/SUBST/
  TOTAL/SCHA12) / 49 lines / 13 diagnostics / 13 hand-computed scenarios / 5 loader-homed FA
  (FA-1040-8283-01..05). IRS_2025_8283_INSTR refreshed to Rev. 12-2025 with verbatim excerpts;
  NEW source USC_26_170F11.
- **Ken's review walk (AskUserQuestion): J6 RULED "warn only, feed anyway"** â€” substantiation
  gaps (Â§170(f)(11)(C) appraisal, Â§170(f)(12) vehicle CWA, the attach tier) fire ERROR
  diagnostics while the amount still feeds Schedule A line 12; the withhold recommendation was
  REJECTED (do not re-litigate; FA-04 re-authored to pin the ruling). J2 (nullable capgain
  assertion, default 50% bucket, D_8283_008 warns only when the limitation binds) and J4
  (conservation RED-defer = the ONE feed withhold) as recommended; J1 feeder convention /
  J3 preparer-applied Â§170(e) reductions / J5 one-row-per-group / J7 wet-ink Parts IV-V +
  PDF-attachment e-file note + the stub retirement all approved. Flipped â†’ seeded RS Supabase
  (FlowAssertions 376â†’381) â†’ deployed export verified (51 facts, 0 stale ids; entity_types
  intact) â†’ canonical `server/specs/8283_spec.json` exported to tts.
- `check_8283_integrity.py` (new root gate): independent recompute of all 13 scenarios + the
  Pub 526 T6 worksheet + id caps + citation coverage â€” ALL PASS (re-run after the J6 re-encode).
- **tts build same session â€” UNIT COMPLETE, tag `1040-form-8283-complete`** (flow gate 375â†’380;
  DB pipeline 6/6). Detail â†’ tts STATUS.md / form_coverage_tracker.

---

## 2026-07-03 â€” 4797 classification unit DB-VERIFIED (tts `08c5382`) + NEW confirmed 1065 unrecap-Â§1250 misroute caught
- Ken: "go" â†’ picked the optional **4797 DB pipeline stamp on the entity-side aggregate** (AskUserQuestion).
- Authored **tts `server/tests/test_4797_pipeline_leg.py`** â€” real 1065 FormDefinition (`seed_1065`), real
  `DepreciationAsset` disposition rows, real `compute_return` â†’ `aggregate_dispositions` over the shared
  Supabase test DB. **11/11 green** (the only non-passes across runs were the known transient pooler
  AdminShutdown drops â€” memory `tts-test-db-collisions`; re-ran clean):
  - **TestPipelineClassification (6):** C1 15-yr land improvement 150DB (line 6 ordinary 20k / K10 Â§1231
    180k â€” NOT the Â§1245 100k), C2 SL QIP (ordinary 0 / Â§1231 200k), C3 bonused QIP (ordinary 280k /
    Â§1231 70k), `is_qpp` Building â†’ Â§1245 full recapture (line 6 100k / K10 100k / K9c 0), explicit-1245
    override counterfactual, + the KENFLAG pin. Same numbers as the single-asset unit test, now through
    the production aggregate. Assets use **method=NONE** so `aggregate_depreciation` (runs first and
    overwrites current_depreciation + bonus_amount from the engine) is a no-op â€” the disposition math is
    deterministic off `prior_depreciation` + line-26a additional depr (a live MACRS tail was inflating
    total_depr by 985 in the first draft; method=NONE + folding C3's bonus into prior_depreciation fixed it).
  - **TestPipelineSEBase (1):** the C1 Â§1250 ordinary recapture (line 6 = 20k) rides the 1a-chain into K1
    AND is auto-pulled to WS2, so the box-14a SE base (WS3a) excludes it â€” the exact coupling the
    diagnostics call "misstated through worksheet 1d/2" when the character is wrong.
  - **TestPipelineDiagnostics (4):** `D_4797_CLASS` warns on the auto-Â§1250 Improvements default,
    `D_4797_ADDL` errors on a 150DB asset with a blank 26a, `D_4797_QPP` info fires, and clean Â§1245
    equipment stays quiet.
- **âš  CONFIRMED BUG the stamp caught â†’ Ken: "go ahead" â†’ FIXED same session (tts `f23dc54`):**
  `aggregate_dispositions` was writing the unrecaptured Â§1250 gain to the hardcoded **`K8c`** (a 1120-S
  line) for BOTH forms. The 1065's own line is **`K9c`** (seed_1065.py:288), which `k1_allocator` sends to
  partner K-1 box 9c â€” so on a partnership the value was written to a nonexistent line, silently skipped,
  and never reached the K-1. Fix: form-branched the line (`unrecap_1250_line = "K9c" if 1065 else "K8c"`)
  in both the clear-list and the write, exactly like `ordinary_line`/`k_1231_line`; 1120-S path unchanged.
  Flipped `test_unrecaptured_1250_flows_to_k9c_on_1065` from K9c=0 to **K9c=80000** â€” re-ran green (with
  the prior run, all 11 pipeline tests pass with the fix). Verified the two `test_compute_4797.py` diag
  "failures" seen en route are 1040-path (`_build_return` code=1040 â†’ the fix's `else` branch,
  byte-identical to before) + pooler-storm AdminShutdown drops â€” NOT a regression. Task chip dismissed.
- **NEXT:** (a) the three 4797 depreciation nuances still await Ken's scoping (property-character vs
  recovery-period edge cases, 150DB land-improvement additional depr, bonus-on-QIP Â§1250(b)); (b) K-1
  14b/14c still out of scope (Â§14.4); (c) optionally re-verify the now-fed K-1 box 9c partner pass-through
  (k1_allocator K9câ†’9c) if it surfaces.

---

## 2026-07-02 â€” SCHEDULE_SE R-SE-ROUND: per-line whole-dollar rounding (Ken ruled; the S12 REVIEW_QUEUE item) SEEDED + EXPORTED
- **Ken ruled in-session (AskUserQuestion, the recommended option): Schedule SE adopts the
  per-line whole-dollar convention** â€” the engine's cents-chain (12 = 3,437.44) diverged $1
  from the ATS key / TaxWise per-line math (2,786 + 652 = 3,438) and printed a self-inconsistent
  face (10 + 11 â‰  12 at whole dollars).
- **Authority**: i1040 "Rounding Off to Whole Dollars" fetched fresh (i1040gi.pdf p.23) and
  quoted VERBATIM as a new excerpt on `IRS_2025_1040_INSTR` (the WebFetch summary paraphrased it
  WRONG â€” the PDF quote is canonical; [[webfetch-tax-summary-unreliable]] again).
- **Authored** (`load_1040_schedule_c.py` SE section): NEW rule **R-SE-ROUND** (precedence 0 â€”
  multiplication lines 4a/5b/10/11/13 round their product half-up; sum lines 3/4c/6/8d/12 add
  already-rounded entries; L2 sums cents, rounds the total per the "include cents when adding"
  sentence); L4A/L6/L10/L11/L12/L13 formulas restated with round(); SCHEDSE identity notes;
  **SE-T1..T5 re-pinned whole-dollar** (T5 load-bearing: 4,238 vs cents-chain 4,238.87);
  **FA-1040-SCHSE-02** formula â†’ `round(...,0)` + a rounding constant; rule link R-SE-ROUND â†’
  IRS_2025_1040_INSTR. `check_topic8_integrity.py` `se_part_i` converted to per-line `dollars()`
  (incl. the three load-bearing sanity re-checks) â€” **ALL CHECKS PASS**.
- **Seeded RS Supabase** (idempotent; SCHEDULE_SE rules 13â†’14, all cited). **Deployed export
  verified**: R-SE-ROUND present, L4A formula carries round(), SE-T1 pins whole-dollar, the
  rounding excerpt serves. Canonical `schedule_se_spec.json` refreshed in tts; tts gate file
  `flow_assertions_1040.json` FA-1040-SCHSE-02 synced verbatim (no id drift â€” amended in place).
- **tts build leg same session**: `compute_schedule_se_lines` per-line `_qd`; S12 re-pinned
  (whole-dollar XML values unchanged); Schedule C/8995/7206 audited â€” 7206 already per-line,
  Schedule C sums-only, 8995 Ã—20% lines still cents â†’ flagged to Ken.
- **SAME-SESSION FOLLOW-UP â€” Ken ruled "build it now": 8995 gains R-8995-ROUND** (RS `bfe1d4f`;
  the identical convention: Ã—20% lines 5/9/14 round their product, entries round at entry,
  sums/combines operate on rounded entries; **Form 8995-A explicitly stays cents-chained** â€”
  its own future ruling). Authored: R-8995-ROUND rule + link to the same IRS_2025_1040_INSTR
  excerpt (summary updated to cover both forms); R-8995-L2-L5 / L8-L9 / L13-L14 formulas
  restated; 8995-T2 re-pinned (9,952.20 â†’ 9,952); `check_topic8_integrity.qbi_8995` per-line â€”
  ALL PASS. Seeded (8995 rules 8â†’9), deployed export verified, canonical `8995_spec.json`
  refreshed in tts. tts: `compute_8995_lines` + the 1i-1v face-row writes per-line `_qd`; S12
  re-pinned again (QBI 4,322 whole â†’ taxable 102,373.00 / tax 17,436.06 / owe 6,430.06 â€”
  whole-dollar XML values STILL unchanged). No FA drift (no 8995 FA formula carries a mode).

---

## 2026-07-02 â€” 1065_SE leg 2: the 14a SE-BASE sub-spec SEEDED + EXPORTED (Ken: "approve and seed") + 4797 Â§1245/Â§1250 BUG CONFIRMED
- **Leg 2 (spec Â§4b/Â§14.1)** amends `1065_SE` with the ordinary-income SE base per the IRS "Worksheet
  for Figuring Net Earnings (Loss) From Self-Employment" â€” **text VERIFIED + quoted VERBATIM 2026-07-02
  from the live 2025 i1065 PDF (pymupdf dump, printed p.44-45)**, replacing leg 1's paraphrased excerpts.
- **Authored:** +7 facts (ws 1a/1b/1c/1d/2 inputs + 1e/3a outputs), **+5 rules** (`R-SE-BASE-1B` dealer/
  services-to-occupants rental inclusion [preparer-entered, maid-service-yes/heat-light-trash-no verbatim],
  `R-SE-BASE-1C` other-net-rental K3c inclusion, `R-SE-BASE-4797` Part II line 17 gain-out/loss-back,
  `R-SE-BASE-3A` 1e=1a+1b+1c+1d; 3a=1eâˆ’2, `R-SE-NONIND` no box 14a for estates/trusts/corps/exempts/IRAs
  â€” closes Â§14.5, now worksheet-3b/4b + Code-A grounded, not inferred), **+13 WS lines** (WS1a-WS5),
  **+3 diagnostics** (`D_SE_RENT1B` warning nudge when K2â‰ 0, `D_SE_4797ORD` error when Part II active but
  1d/2 blank, `D_SE_NONIND` info), **+7 scenarios** (B1-B7 incl. the 3a sign rule B6: âˆ’5kâˆ’10k=(15k)),
  **+INV-SE-BASE** (active) â€” FLOW-14A-SE stays disabled. New `check_1065_se_integrity.py` math gate
  (independent re-type of the classification table + worksheet; loader & gate share no math) â€” ALL PASS.
- Ken walked the 3 design calls (1b preparer-entered+nudge; D_SE_4797ORD hard error until the 4797 engine
  feeds 1d/2; B-scenario values) â†’ **"approve and seed"**. Seeded RS Supabase (idempotent; "Updated
  1065_SE": 18 facts / 14 rules / 25 links / 15 lines / 6 diags / 17 scenarios; **FlowAssertions â†’ 371**,
  all rules cited) â†’ re-exported `1065_se_spec.json` (59 KB) â†’ **tts handoff committed (`e5f2795`)**:
  spec JSON + seed_1065_se EXPECTED bumped (re-ran clean) + test_1065_se_compute_leg partitions B1-B7 as
  NAMED pending-skips (47 passed, 7 skipped) â€” the base compute + non-individual guard are the next tts
  build leg.
- **âš  COUPLED VERIFICATION (spec Â§4b) â€” REAL BUG CONFIRMED in tts:** `resolve_recapture_type()`
  (tts compute.py:1272-1290) classifies Improvements by RECOVERY PERIOD (life <27.5 â†’ Â§1245), so a 15-yr
  QIP/land improvement sold at a gain takes FULL ordinary recapture instead of Â§1250 treatment
  (additional-depreciation-over-SL only; remainder unrecaptured Â§1250 â†’ K-1 9c) â€” and
  `test_improvements_15yr_is_1245` PINS the bug. Propagates into box 14a via ws 1d/2. RS 4797 Part III
  math is correct once property_type is known â€” the defect is the tts auto-classification input.
  **Ken-flagged nuances (his call, NOT decided here):** (1) not all 15-yr is Â§1250 (single-purpose ag
  structures are Â§1245) â€” property character, not life, is the classifier â†’ likely a per-asset
  determination + diagnostic (the se_classification pattern); (2) land improvements at 150DB DO have
  additional depreciation â†’ partial ordinary recapture; (3) whether BONUS on QIP is Â§1250(b) additional
  depreciation â€” UNVERIFIED, do not guess. Recommended: its own RS-spec'd unit.
- **NEXT:** (a) tts build leg â€” base compute (worksheet 1a-3a) + R-SE-NONIND guard, un-skip B1-B7;
  (b) the 4797 recapture-classification RS unit (Ken to scope); (c) K-1 14b/14c still out of scope (Â§14.4).

---

## 2026-07-02 (MeF track, ATS Scenario 12) â€” NEW FORM_7217 spec AUTHORED + KEN-APPROVED + SEEDED + EXPORTED
- **Ken approved in-session** (AskUserQuestion, four items): **J1 RULED "wire Â§731(a)(1) gain to
  Sch D now"** (over the recommended defer) â€” post-ruling amendment encodes a synthesized
  no-1099-B Form 8949 row (Part I box C ST / Part II box F LT per a NEW holding-period preparer
  assertion `f7217_interest_held_lt`; proceeds = line 5c, basis = line 6; unasserted â†’ feed
  WITHHELD + NEW **D_7217_011** RED; **D_7217_002** re-purposed to the info "auto-reported"
  transparency role; outputs `f7217_8949_st/lt`; scenarios T10/T11 added, G1 re-pinned; FA-04
  reworded + NEW **FA-1040-7217-05**) â€” the landing verified VERBATIM against the 2025 Partner's
  Instructions for Schedule K-1 (Form 1065) box 19 ("should be reported on Form 8949 and the
  Schedule D"; NEW source **IRS_2025_K1P_INSTR**, also carrying the Â§737 4797-or-8949 excerpt
  that backs the J3 defer). J2 Â§731(a)(2)-loss + J3 Â§737 defers KEPT; J4 rounding / J5
  classification-withhold / J6 securities feeder approved as encoded; the T1 answer-key
  divergence acknowledged.
- **Integrity gate re-run post-amendment: ALL CHECKS PASS** (18 scenarios / 31 facts / 5 rules /
  23 lines / 11 diagnostics / 5 FAs). **Seeded RS Supabase** (FORM_7217 created, TaxForms 78,
  all rules cited). **Deployed export id-verified: PASS** (5/11/23/31/18 exact â€” NOTE the lookup
  key is `FORM_7217`; the bare-number `7217` 404s). **FA drift check: RS 1040 export 353 vs tts
  gate 348 â€” delta EXACTLY FA-1040-7217-01..05, zero other drift.** Canonical `7217_spec.json` +
  `flow_assertions_1040_7217_pending.json` â†’ tts `server/specs/` (ASCII-escaped). tts four-leg
  build next. *(Coordination note: a parallel 1065_SE session committed fc93643 mid-unit, which
  swept in this unit's in-flight check_7217_integrity.py J1 edit â€” content verified intact.)*
- *(Authoring detail below, written pre-ruling â€” the J1 items superseded per the amendment above.)*
- **Trigger:** ATS Scenario 12 (Sam Gardenia) is the next smallest-first scenario (Ken's 2026-07-02
  ruling); its tax-law form â€” Form 7217, Partner's Report of Property Distributed by a Partnership
  (Â§732) â€” had no RS spec (lookup 404, the process gate). The SEASON_PLAN appendix-4 OBBBA check ran
  at the spec leg: Â§732 is a basis provision, not a credit â€” NO sunset; amendment history stops at
  P.L. 106-170 (1999), OBBBA untouched; the Dec-2024 form/instructions revision is current. One
  post-publication development FOUND and encoded: the IRS 2026-04-27 update re-sources lines 3/5a/5b
  to NEW K-1 (1065) box 19 codes for TY2025+ (line 3 â† B/C/G + the A/F securities statement; 5a â†
  A/D/F excl. securities; 5b â† the A/F statement; instructions revision announced for Dec 2026) â€”
  sourcing hints only, math unchanged.
- **`load_1040_form_7217.py` (NEW):** 28 facts (distribution-level + per-property Part II rows) /
  5 rules (R-7217-FILE per-date+money-only+Â§751(b)+claim-year screens; -GAIN Â§731(a)(1) lines 5-8;
  -L9L10 the Â§732(a)(2)/(b) allocable-basis mechanic incl. the i7217 line-9 Â§737-include +
  5a-only-subtraction literal reading; -ALLOC the FULL Â§732(c) waterfall â€” hot assets at basis
  first (decrease-only tier), other property with (c)(2) increase / (c)(3) decrease; -LOSS the
  Â§731(a)(2) liquidating-loss detection, the one lawful line-10 â‰  B(e) case) / 23 lines / 10
  diagnostics / **16 HAND-COMPUTED scenarios** (T1 = ATS-12 facts under enacted law â€” âš ï¸ the IRS
  key's own Part II is internally inconsistent (col (e) 4,000 vs its line 10 = 6,000) and lists
  "CASH" as a Part II property; T2/T3 pin the i7217's OWN Examples 1 & 2 verbatim incl. the worked
  100/440/110 waterfall; every (c)(1)(A)/(B), (c)(2)(A)/(B), (c)(3)(A)/(B) branch + gain / loss /
  Â§737 / securities / unclassified / money-only / claim-year edges) / 4 loader-homed
  FA-1040-7217-01..04. Sources: NEW USC_26_732 + USC_26_731 + IRS_2024_7217_INSTR (incl. the
  box-19 update excerpt) + IRS_2024_7217_FORM, all key passages verbatim, requires_human_review set.
- **Gate:** NEW `check_7217_integrity.py` â€” an INDEPENDENT Â§732(c) transcription (statute-direct,
  self-tested against the IRS Example-2 answer before checking the loader) + full per-scenario
  recompute + varchar(20) id guards + structure checks â€” **ALL CHECKS PASS** (16 scenarios). The
  gate caught one authoring gap live (D_7217_004 unexercised â†’ scenario 7217-G7 added).
- **NOT seeded** â€” READY_TO_SEED=False; refusal verified. Six judgment items J1-J6 queued for
  Ken's review walk (gain/loss/Â§737 RED-defers; rounding; classification withhold; securities
  feeder) + the T1 answer-key divergence.
- tts build (PartnershipDistribution + DistributedProperty models, compute_7217, input tab,
  AcroForm render, FA merge, then the Scenario-12 mapper) follows in tts-tax-app after approval.

---

## 2026-07-02 (MeF track, ATS Scenario 13) â€” NEW FORM_8911 spec AUTHORED + SEEDED + EXPORTED
- **Trigger:** ATS Scenario 13 (Birch) is the next smallest-first scenario unit (Ken's 2026-07-02
  ruling); its tax-law form (8911 + Schedule A) had no RS spec (lookup 404 â€” the process gate).
  The SEASON_PLAN appendix-4 **OBBBA sunset check ran at this spec leg as required**: Â§30C(i) as
  amended by P.L. 119-21, fetched VERBATIM (law.cornell.edu + i8911 Rev. 12-2025) â€” "This section
  shall not apply to any property placed in service after June 30, 2026." â†’ **TY2025 fully live,
  TY2026 HALF-YEAR live (Janâ€“Jun installs), TY2027+ dead. NOT zero TY2026 value â€” no S13 re-rule.**
- **Ken approved in-session** (AskUserQuestion, all four judgment items): (1) the line-6b ORDERING
  reading â€” the verbatim instruction sums Sch 3 "lines 2 through 5, and 7 (reduced by 6a/6b/6k)";
  line 7 literally includes 8911's own 6j â†’ encoded as "all Part-I credits ordered before 8911,
  never its own 6j"; (2) census tract = PREPARER ASSERTION v1 (GEOID 11-digit format validated,
  Appendix A/B NOT adjudicated; unanswered â†’ D_8911_001 RED + excluded, answered No â†’ quiet stop);
  (3) business path computes on the face but RED-defers to the unbuilt Form 3800 (D_8911_004,
  line 3 + K-1 line 2 never land on Sch 3); (4) the T1 enacted-law pins â€” the IRS ATS-13 answer
  key used the PRE-OBBBA 30,000 MFJ std deduction (tax 162/credit 162); enacted law (31,500) â†’
  tax 11/credit 11; the engine follows enacted law, ATS acceptance is schema + business rules.
- **`load_1040_form_8911.py` (NEW):** 16 facts (per-property Sch A rows + return-level K-1) /
  5 rules (R-8911-QUALIFY window+claim-year+tract, -SCHA-PERS 30%/$1,000-per-item, -SCHA-BUS
  6%-30%PWA/$100,000 + Â§179 backout + 1/29/2023 auto-Yes, -TAXLIM L5-L9 with TMT-figured-always
  = FORM_6251 line 9, -SCH3-6J min(L4,L9) + excess LOST) / 35 lines (form + "A-" prefixed Sch A) /
  6 diagnostics / 10 HAND-COMPUTED scenarios (Birch enacted-law exact; $1,000 cap; TMT bite;
  **6/30â†”7/1/2026 boundary pair**; tract No vs UNANSWERED; business RED; mixed-use 6%; 6b
  exact-fit; claim-year trap) / 4 loader-homed FA-1040-8911-01..04. Sources: NEW USC_26_30C +
  IRS_2025_8911_INSTR + IRS_2025_8911_FORM, all key passages verbatim, requires_human_review set.
- **Gate:** NEW `check_8911_integrity.py` â€” independent re-typed constants + full per-scenario
  recompute + the varchar(20) id guards â€” **ALL CHECKS PASS** (pre- and post-flip).
- **Seeded RS Supabase** (FORM_8911 created; TaxForms 77, FlowAssertions 370 rows). **Deployed
  export verified id-level** (5/6/10/35/16 exact, all ids match). **FA drift check: RS 1040 export
  348 vs tts gate file 344 â€” delta EXACTLY FA-1040-8911-01..04, zero other drift** either
  direction. Canonical `8911_spec.json` exported to tts `server/specs/`.
- tts build (RefuelingProperty list model, compute_8911, input tab, AcroForm render, FA merge,
  then the Scenario-13 mapper: IRS6251 + IRS8911 + IRS8911ScheduleA) follows in tts-tax-app.

---

## 2026-07-02 (MeF track, later) â€” R-8959-ENGAGE amendment: Who-Must-File engage gate SEEDED + EXPORTED
- **Trigger:** ATS Scenario 5's W-2 (box 5 = 31,232 / box 6 = 453, a whole-dollar-rounded 452.86)
  made compute put $0.14 on 1040 line 25c â€” the code's 'line 22 > 0 engages' arm (never in the
  spec) treats ANY box-6 excess as Additional Medicare withholding. The 2025 i8959 Who Must File
  (fetched + quoted VERBATIM, rev. Aug 7 2025) lists FOUR conditions only; a box-6 excess is not
  one â€” and both spec and code MISSED bullet 1 (any SINGLE W-2 box 5 > $200,000 FLAT â€” the
  employer-withholding case, e.g. one 210k W-2 on an MFJ return under the 250k threshold).
- **Ken approved in-session** (AskUserQuestion): bullet-1 arm added, line-22 arm removed,
  D_8959_003 engage-gated.
- **`load_1040_schedule_c.py`:** +fact `amt_max_single_w2_medicare_wages`; R-8959-ENGAGE formula =
  the three Who-Must-File arms (RRTA bullets stay RED-deferred); D_8959_003 condition gains
  `form_8959_engaged`; +scenarios 8959-T6 (HAND-COMPUTED: MFJ one 210k W-2 â†’ engages via bullet 1,
  L21 3,045 / L22 = L24 = 90 â†’ 25c; L18 = 0) and 8959-T7 (the Scenario-5 rounding artifact â†’
  NOT engaged, 25c untouched, D_8959_003 quiet); +NEW source `IRS_2025_8959_INSTR` with the
  verbatim Who-Must-File excerpt + R-8959-ENGAGE link.
- **Gate:** `check_topic8_integrity.py` extended (amt_8959 gained the max-single-W2 engage arm +
  T6/T7 re-derivation blocks) â€” **ALL CHECKS PASS**.
- **Seeded RS Supabase**; deployed 8959 export verified (only the intended deltas); SIBLING exports
  (SCHEDULE_C / SCHEDULE_SE / 8995) id-diffed vs their tts canonical files â€” **zero sibling drift**
  (the sibling-spec re-export lesson). Canonical tts `8959_spec.json` replaced.
- tts: `form_8959_engaged` reshaped (max_single_w2 arm, line-22 arm gone) + `max_single_w2_box5`
  shared helper (compute + all three D_8959_* diagnostics â€” bridge-gate); tests updated (trip-wire
  5â†’7, engage-gate cases). ATS Scenario 5 re-probe: 22/22 pinned lines match, 25d = 1,754 exactly.

---

## 2026-07-02 (MeF track) â€” SCH_8812 ACTC opt-out amendment + spine PECF facts SEEDED + EXPORTED
- **Trigger:** MeF ATS Scenario 5 (Bobby Barker) checks the 2025 Form 1040 line-28 box â€” official
  face verbatim: "Additional child tax credit (ACTC) from Schedule 8812. If you do not want to
  claim the ACTC, check here" (e-file `DoNotClaimACTCInd`, 2025v5.4). compute_8812 had no election.
- **Ken approved in-session** (AskUserQuestion): skip-Part-II-A-entirely semantics (16aâ€“27 zero,
  1040 line 28 = 0; CTC/ODC line 14 â†’ line 19 NEVER touched).
- **`load_1040_ctc.py`:** +fact `actc_opt_out` (return-level election, default false); R017
  formula/inputs gain `AND NOT actc_opt_out`; +D014 (info transparency â€” elected with QCs
  present); +TS19 (HAND-COMPUTED: HOH, 2 QC, tax 500 â†’ L_14 500 kept, forfeits the 3,400 ACTC);
  +FA-1040-CTC-13 (`conditional_zero`, trigger actc_opt_out â€” loader-homed, no export drift);
  +verbatim line-28 excerpt on the EXISTING `IRS_2025_1040_FORM` source (LOOKUP-attach, never
  update_or_create over a shared source row) + R017 link. Docstring counts refreshed.
- **`load_1040_spine.py`:** +facts `pecf_primary` / `pecf_spouse` (Presidential Election Campaign
  header boxes â€” stored, no compute effect; e-file `PECFPrimaryInd`/`PECFSpouseInd`). The
  lived-apart (`mfs_hoh_lived_apart_last_6_months`) and main-home-US (`us_home_more_than_half_year`)
  facts ALREADY existed. Fixed the stale "no blind flag exists in tts" notes (model has both).
- **Seeded RS Supabase** (both loaders; RuleAuthorityLinks 975â†’971 wobble = the known 1040-stub
  supersession cycle between the two loaders, both link-gates green). **Deployed export verified:**
  SCH_8812 39 facts / 13 diagnostics / 19 tests, R017 amended, TS19 exact; FA export 344 = tts
  gate 343 + exactly FA-1040-CTC-13, zero other drift either direction. Canonical
  `sch_8812_spec.json` + `1040_spine_spec.json` re-exported to tts same sitting.
- tts build (model field, compute gate, input, render, FA merge) follows in tts-tax-app.

---

## 2026-07-02 (later) â€” GA-500 W7 amendment: HB 463 tips/overtime exclusions SEEDED + EXPORTED
- **Ken approved in-session** (AskUserQuestion Ã—2: the four scope forks â€” full unit / per-taxpayer
  cap / assertion+auto-feed / dedicated S1-12a-12b sub-lines â€” then the seed go-ahead after the
  review-packet walk).
- **The law:** enacted HB 463/AP (signed 2026-05-11; legis.ga.gov doc 249080) Â§48-7-27(a)(16)
  qualified overtime / (a)(17) cash tips â€” each â‰¤$1,750, TY2026-2028, both self-repeal 12/31/2028.
  Verbatim text fetched + quoted (the tts-side statute verification earlier the same day).
- **Loader `load_ga500_form_500.py`:** +6 facts (per-owner tips/OT bases + FT-hourly assertions),
  +rules R-GA500-TIPS / R-GA500-OT (window-gated, PER-TAXPAYER cap, OT assertion gate, W-2-only
  OT source, RAW federal bases â€” GA has no phaseout), R-GA500-L9-S1 amended (subs run L7-L12b),
  +lines S1-12a/S1-12b, +diagnostics D_GA500_013 (OT-unasserted nudge) / 014 (tips-attestation
  nudge) / 015 (out-of-window error), +scenarios GA500-T15..T18 (HAND-COMPUTED: per-taxpayer caps
  3,500/2,750 â†’ tax 4,179; unasserted-OT zero â†’ 2,246; TY2025 year gate â†’ 2,491; under-cap
  passthrough â†’ 1,672), +FA-GA500-13/14, +4 rule-authority links, W7 walk item documented.
- **HB 463 authority CORRECTED:** the prior summary excerpt WRONGLY dated the std-deduction
  increase 2027; replaced with 5 VERBATIM /AP excerpts (effective date Â§5-1, strike-and-insert
  rate/std/dep text, both exclusion paragraphs, RIE (xiii)/(xiv) timing); the seed deletes the
  stale excerpt row by its old label (excerpts key on source+label). Source citation/trust
  updated (doc 249080, 10.0).
- **Gate:** `check_ga500_integrity.py` extended (independent re-typing: window helper, per-owner
  caps, S1-13/14 now emitted) â€” **ALL CHECKS PASS** (constants + helpers + LIC + 18 scenarios).
- **Seeded RS Supabase:** form 500 now 83 facts / 23 rules / 91 lines / 15 diagnostics / 18
  scenarios / 14 FA. Deployed export re-fetched â†’ canonical tts `server/specs/500_spec.json`
  replaced; id-level drift check: only R-GA500-L9-S1 (intended) + two rules' embedded authority
  metadata (the corrected source row) changed â€” zero content drift otherwise. FA-GA500-13/14
  merged into the tts gate file (341â†’343 assertions; gate 363â†’365) â€” loader homes exist HERE, so
  no export drift (the fa-needs-rs-loader-home rule).

---

## 2026-07-02 â€” FA drift resolved: RS DB re-synced to the tts canonical gate (export 341 = file 341)
- REVIEW_QUEUE 2026-07-01 item; **Ken chose "re-seed RS now; tts file stays canonical"** (in-session).
- **Root cause:** the 21 missing assertions never had loader homes. FA-1040-2441-07 and the six
  FA-1040-5329-* existed ONLY in the tts gate file (merged there during their units); load_sch_1a.py
  still carried the pre-rename FA-1040-SCH1A-01..07 block. The tts canonical set = the 14 renamed
  FA-SCH1A-* PLUS the retained legacy-id 05/06/07; only 01..04 were superseded.
- **Changes (transcription was MECHANICAL â€” scripted from the canonical JSON, no re-authoring; all
  21 were already Ken-approved via their tts units):**
  - `load_sch_1a.py` â€” FLOW_ASSERTIONS block replaced with the canonical 17 (14 FA-SCH1A-* +
    legacy 05/06/07 verbatim); the seed now DISABLES the superseded 01..04 (the export serves
    status="active" only; rows stay auditable) and forces-active everything the block owns.
  - `load_1040_form_2441.py` â€” +FA-1040-2441-07 (sort 7).
  - **NEW `load_1040_5329.py`** â€” FA-only loader (six FA-1040-5329-*); documents the boundary:
    no 5329 form spec is authored in RS yet â€” that remains open work with its own future
    READY_TO_SEED review.
- Seeded RS Supabase (FlowAssertions rows 342â†’363 incl. disabled); deployed
  `/api/flow-assertions/export/?entity_type=1040` verified by id-level diff: **341 = 341, zero
  drift both directions.** Routine re-exports are clean again. tts gate file untouched.

---

## 2026-07-01 â€” FORM_2210: dated Â§6654 accrual amendment SEEDED + EXPORTED
- **Ken chose scope option 1 in-session ("build as designed", tts
  `server/specs/2210_dated_penalty_design.md`)** â€” that approval covers this amendment + seed
  (the form's READY_TO_SEED was already True from the 2026-06-15 review walk).
- **The change:** R-2210-REG reworded from the fixed due-dateâ†’4/15/2026 day count (DAYS_7/DAYS_6
  arrays) to the i2210 Penalty Worksheet rule its own authority excerpt already stated verbatim â€”
  each payment applies to the EARLIEST still-underpaid installment and the underpayment accrues
  from its due date to the date cured, capped 4/15/2026 (7%â†’6% split at 3/31/2026). Withholding
  stays Â¼-spread ON the due dates (Â§6654(g) default; the actual-date election remains deferred).
  Loader pure functions rewritten to the unified dated algorithm (`days_at_rates` + earliest-first
  event loop; `underpayments` = the at-due-date face-25 values); `compute_2210` gained
  `payments_dated`. NEW fact `t2210_payments_dated`; NEW scenarios **P-T7 (mid-year lump, 217)** /
  **P-T8 (Q4 paid 1/25/2026, 5)** â€” both HAND-COMPUTED; P-T1..T6 unchanged (due-date payments
  reproduce the old numbers exactly â€” the backward-compat pin). FA-02/03 reworded; NEW
  **FA-1040-2210-07** (dated payments stop accrual on the date paid).
- **`check_2210_integrity.py` extended** â€” its independent transcription now re-types the dated
  algorithm (event loop + its own day counter) + pins the DAYS_7/DAYS_6 equivalence at the cap and
  the zero-days-on-time boundary. **ALL CHECKS PASS** (11 facts / 3 rules / 11 lines / 5 diags /
  9 scenarios / 5 links / 7 FAs).
- Seeded RS Supabase (`update_or_create`; TaxForms 76 unchanged, **FlowAssertions 341â†’342**).
  Deployed export fetched â†’ canonical **tts `server/specs/2210_spec.json` replaced** (semantic
  diff = exactly ~R-2210-REG, +t2210_payments_dated, +P-T7/P-T8; diagnostics/lines/authorities
  untouched).
- **Same-session follow-ups:** (`9f94b7b`) +diag **D_2210_DATED** (dated-vs-line-26 reconciliation
  warning) + P-G2 scenario + creditable-kind conventions in the fact notes â†’ re-seeded (10 scenarios,
  6 diagnostics) + re-exported. (`0b72b6f`) the tts FA-03 gate caught my pure function blending the
  form's TWO allocations â€” fixed: FACE line 25 = per-column DATE-WINDOW netting (+overpay carry);
  PENALTY = the earliest-first date-cured worksheet; FA-03 reworded to state both; gate ALL PASS,
  re-seeded (FA text only).
- tts legs shipped same session â€” tag `1040-2210-dated-payments-complete` (6 DB pipeline tests green,
  incl. the dated-late-Q4 = 4.00 hand-computed pin).

---

## 2026-07-01 â€” 1065_SE: Schedule K / K-1 line 14a Self-Employment (SECA) SEEDED + EXPORTED
- New form `1065_SE` (entity_type 1065, TY2025, draft) authored from the LOCKED spec
  `tts-tax-app/server/specs/1065_se_line14a_spec.md` (tax-law decisions locked by Ken 2026-07-01;
  faithful translation only â€” no tax-law calls made here). New loader `load_1065_se.py`, mirrors the
  `load_1040_schedule_k1.py` idiom (READY_TO_SEED guard + hollow-seed guard + single `@transaction.atomic`,
  `update_or_create` throughout â†’ idempotent, no partial writes; a first run tripped varchar(255) on the
  case-law `citation`, shortened, re-ran clean).
- **Governs:** Sch K line 14a + per-partner K-1 box 14 code A. The one modernization vs today's silent
  compute: substitutes a per-partner functional-analysis `se_classification` (active/passive/undetermined)
  for the IRS SE Worksheet's mechanical "limited partner" label at lines 3b/4b (post-*Soroban* an *active*
  limited partner is not a "limited partner, as such" under Â§1402(a)(13)). Entity 14a derived BOTTOM-UP =
  Î£ per-partner box 14a (replaces the independent `K14a = K1 + K4c`). SE base itself OUT OF SCOPE (Â§14).
- **Authored:** 7 authority sources (IRC Â§1402 / Â§702 / Â§707(c); Treas. Reg. Â§1.1402(a)-1 & -4; the
  limited-partner case line Renkemeyer/Soroban I+II/Denham/contra-Sirius; IRS i1065 2025 SE Worksheet p.45)
  + 1 topic; 11 facts; **9 rules** (R-SE-CLASS, -DSHARE, -GPSVC, -GPCAP, -DEFAULT, -RENTAL, -PORT, -LOSS,
  -14A-ENT) with **18 RuleAuthorityLinks (all rules cited)**; 2 lines (`K14a`, `14a`); **3 diagnostics**
  (D_SE_UNDET error, D_SE_GPCHAR warning, D_SE_RECON error); **10 tests** (T1â€“T10, expected 14a locked);
  **3 flow assertions** (RECON-14A + INV-CHAR active; **FLOW-14A-SE seeded status=disabled** = future/inactive).
- **CFR/USC text READ DIRECTLY and quoted VERBATIM 2026-07-01** (Cornell LII mirror; eCFR geo-blocked
  automated fetch): Reg Â§1.1402(a)-1(a)(2) & (b) [note (a)(2) says "section 702(a)(9)" â€” the reg's own
  pre-renumbering cross-ref, quoted as-is], Reg Â§1.1402(a)-4(a), IRC Â§1402(a)/(a)(1)/(a)(2)/(a)(3)/(a)(13),
  Â§707(c), Â§702(a)(8)/(b). Case-law group carries the "verified 2026-07-01 / re-verify each season" note
  (`requires_human_review=True`; developing circuit split, Soroban 2nd Cir. / Denham 1st Cir. appeals pending).
- Seeded RS Supabase (`update_or_create`; **TaxForms 75â†’76, FlowAssertions 338â†’341**). Ran dev server â†’
  `GET /api/forms/lookup/1065_SE/export/` returns HTTP 200 â†’ wrote **`1065_se_spec.json`** (38 KB, repo root):
  9 rules / 3 diagnostics / 10 tests / 7 authority_sources / 2 lines, all rules cited. Active-assertions
  export (`?entity_type=1065`) correctly excludes the disabled FLOW-14A-SE.
- **DoD met; STOPPED as instructed.** The tts `seed_*` loader + `compute_self_employment` rewrite are a
  SEPARATE tts-tax-app session, gated on this export being fetchable (do NOT touch tts compute here).
  Coupled follow-up (spec Â§4b/Â§14): the SE-base sub-spec (i1065 worksheet 1aâ€“3a Form-4797/rental
  adjustments) is coupled with the 4797 Â§1245-vs-Â§1250 recapture verification.

---

## 2026-07-01 â€” SCHEDULE_A: line 5a state-income-tax auto-aggregation amendment SEEDED + EXPORTED (Ken go-ahead)
- Ken's UX/bug batch item "state withholding â†’ Schedule A". Ken chose (tts AskUserQuestion) the FULL scope
  (withholding + estimates + prior-year taxes + prior-year extensions, with payment DATES) AND the full RS
  round-trip. Line 5a was a single hand-keyed fact (`scha_salt_income_or_sales`); it now AUTO-TOTALS the
  return's state/local income tax. `load_1040_schedule_a.py` amended:
  - **+4 facts** â€” `scha_state_income_tax_withheld` (derived Î£ doc withholding, YELLOW),
    `scha_state_estimated_payments` + `scha_state_prioryear_tax_paid` (aggregates of a new tts
    `StateIncomeTaxPayment` child table, filtered to date_paid in the tax year),
    `scha_line5a_state_income_total` (the YELLOW auto-total = withheld + estimated + prior-year).
  - **+1 rule** `R-SCHA-5A-STATE` (precedence 2, BEFORE R-SCHA-SALT â€” it feeds line 5d). Line 5a DEFAULTS to
    the auto-total (YELLOW) unless general sales taxes are elected (`scha_use_sales_tax` â†’ the sales figure)
    or `scha_salt_income_or_sales > 0` is a direct override (GREEN wins). Â§164 cash-basis: deductible in the
    year PAID (a Q4 estimate paid in January is next year's). Existing rules 2-7 precedence-bumped to 3-8
    (ordering metadata only; no logic drift â€” confirmed by field-level diff).
  - **+2 diagnostics** â€” `D_SCHA_010` (info, transparency: 5a auto-totaled from W/E/P; verify complete; note
    that mandatory CA/NJ/NY SDI/UI/family-leave contributions are NOT auto-included), `D_SCHA_011` (info,
    no-silent-gap: a payment dated outside the tax year is excluded from 5a).
  - **+5 scenarios** SCHA-T12..T16 (withholding-only; WH+estimates+prior-year; Jan-paid Q4 excluded;
    direct-entry override GREEN; sales-tax election suppresses). **+2 flow assertions** FA-1040-SCHA-07/08.
  - **+1 authority** `IRS_2025_SCHA_INSTR` â€” the 2025 Instructions for Schedule A "Line 5a" text, fetched +
    quoted VERBATIM 2026-07-01 (withholding from W-2/W-2G/1099-G/R/MISC/NEC; prior-year tax paid this year;
    estimates incl. a prior-year refund credited forward; mandatory SDI/UI/family-leave; NOT refunds). Linked
    to R-SCHA-5A-STATE (primary) + the form face (secondary).
- **Math is a sum + a Â§164 date filter â€” no new numeric constants.** `check_schedule_a_integrity.py` extended
  (independent `ind_line5a_total` / `ind_line5a_final` recompute; D_SCHA_010/011 in DIAG_KEYS) â†’ ALL CHECKS
  PASS (facts 26â†’30, rules 7â†’8, diags 9â†’11, scenarios 12â†’17, links 10â†’12, FA 6â†’8). Seeded RS Supabase
  (`ylqaejdqwuvwpglxnpgv`, idempotent `update_or_create`; FlowAssertions 336â†’338, TaxForms 74, all rules
  cited) â†’ re-exported `/api/forms/lookup/SCHEDULE_A/export/` â†’ overwrote tts `server/specs/schedule_a_spec.json`
  (semantic diff: ONLY the 4 facts + 1 rule + 2 diags + 5 tests added, 6 precedence bumps; zero content drift).
- **tts build (compute/model/render/input/diagnostics/tests) is the next leg** â€” the `StateIncomeTaxPayment`
  child model + the withholding aggregation (W2StateEntry rows, else the legacy flat field; 1099-R/INT/DIV,
  1099-G, W-2G) â†’ line 5a. Federal payment-date capture for Form 2210 UET is a SEPARATE next unit (Ken's
  sequencing choice).

---

## 2026-07-01 â€” FORM_8606: Roth basis tracker (year-over-year line 22/24) amendment SEEDED + EXPORTED (Ken go-ahead)
- Ken's UX/bug batch item "Roth basis tracker â€” year-over-year Roth contribution basis (8606 Part III only
  captures at distribution)". Ken chose (tts AskUserQuestion) contribution+conversion cumulative scope AND the
  full RS round-trip (compute_8606 is spec-governed). `load_1040_8606.py` amended:
  - **+1 fact** `f8606_roth_cy_contributions` (decimal) â€” current-year regular Roth contributions. NOT an 8606
    line: a regular Roth contribution needs no 8606, so it's recorded on the per-owner Roth basis tracker
    (tts `RothIRABasis`) and the proforma roll adds it to next year's line-22 basis.
  - **+1 routing rule** `R-8606-ROTHTRACK` â€” line 22 (contribution basis) + line 24 (conversion basis) are
    SOURCED from the per-owner tracker (opening carryforward, YELLOW), overridable direct-entry (GREEN). The
    year-over-year roll is stated exactly: a distribution recovers contribution basis FIRST tax-free, so
    next line 22 = max(0, l22 âˆ’ l21) + cy_contributions (l21 = roth_dist âˆ’ homebuyer); next line 24 =
    max(0, l24 âˆ’ max(0, l21 âˆ’ l22)) + this year's conversions (line 8). Cited IRC_408A (Â§408A(d)(4)) +
    i8606 Part III.
  - **+1 diagnostic** `D_8606_ROTHNOBASIS` (warning) â€” nonqualified Roth distribution present with zero
    recorded contribution+conversion basis â†’ the whole distribution is taxed as earnings (line 25c); nudge to
    enter the cumulative basis / use the tracker. Closes a silent over-taxation gap. + scenario F-G2.
- **Part III math UNCHANGED** â€” Â§408A(d)(4) ordering was already verified/cited; the tracker is a records-keeping
  carryforward, not new law. The roll formula was hand-verified against two worked examples (full + partial basis
  recovery). `check_8606_integrity.py` ALL CHECKS PASS (facts 16â†’17, rules 4â†’5, diags 6â†’7, scenarios 8â†’9,
  links 6â†’8; the Â§408(d) pro-rata + Â§408A ordering still re-type to the dollar). Seeded RS Supabase
  (`ylqaejdqwuvwpglxnpgv`, idempotent `update_or_create`) â†’ re-exported `/api/forms/lookup/FORM_8606/export/` â†’
  overwrote tts `server/specs/8606_spec.json` (semantic diff: ONLY the 4 additive items; zero drift on existing
  content). +1 flow assertion `FA-1040-8606-07` (in the FlowAssertion table, 336 total; not in the form export â€”
  wired tts-side in flow_assertions_1040.json). tts DiagnosticRule rows re-seed on the next Render deploy.

---

## 2026-07-01 â€” FORM_1116: Â§904(j) de minimis AUTO-election amendment SEEDED + EXPORTED (Ken go-ahead)
- Ken's UX/bug batch item "foreign-tax de minimis (Â§904(j))". Ken chose (tts AskUserQuestion) auto-apply +
  opt-out AND the full RS round-trip (the diagnostics are spec-governed). `load_1040_form_1116.py` amended:
  - **+1 fact** `f1116_deminimis_optout` (boolean, return-level opt-out; stored on tts `Taxpayer`, NOT on a
    Form 1116 row â€” the auto-path must work with no Form 1116 engaged).
  - **`R-1116-ELECT` reworded** â€” the Â§904(j) election now applies AUTOMATICALLY when the only foreign tax is
    from 1099-INT/1099-DIV (passive + payee-statement by definition), total â‰¤ $300/$600, no full Form 1116
    engaged, and not opted out (else the existing manual `elect_simplified`). Same math: min(foreign tax,
    regular tax) â†’ Sch 3 L1, no carryover.
  - **`D_1116_001` reworded** ('available / check the box' â†’ 'applied automatically'); stays info.
  - **+1 diagnostic** `D_1116_009` (warning) â€” over-ceiling nudge: 1099 foreign tax > ceiling with no Form 1116
    engaged â†’ the credit is unclaimed; file the full Form 1116 or deduct on Sch A. Closes a silent gap.
    App-layer condition (reads the 1099 aggregate + no-Form-1116-row) â†’ no pure compute_1116 scenario.
- **Math UNCHANGED** â€” the Â§904(j) conditions were re-verified verbatim vs i1116 + 26 USC Â§904(j) (no new law).
  `check_1116_integrity.py` ALL CHECKS PASS (facts 19â†’20, diagnostics 8â†’9, rules 5, all scenarios recompute to
  the dollar). Seeded RS Supabase (`ylqaejdqwuvwpglxnpgv`, idempotent, `update_or_create`) â†’ re-exported
  `/api/forms/lookup/FORM_1116/export/` â†’ overwrote tts `server/specs/1116_spec.json` (semantic diff: ONLY the
  opt-out fact + D_1116_009 added, D_1116_001 message + R-1116-ELECT text changed; zero drift). tts DiagnosticRule
  rows re-seed on the next Render deploy (build.sh idempotent seed_rules).

---

## 2026-06-30 â€” Default-to-No due-diligence questions: D_1040_017 + D_SCHB_001 severity amendment SEEDED + EXPORTED (Ken go-ahead)
- Part of Ken's UX/bug batch. Ken chose the "proper RS round-trip now" path (tts AskUserQuestion) after CC
  flagged that the tts code change touched spec-governed diagnostics. Two loaders amended:
  - **`load_1040_spine.py`** â€” `D_1040_017` (digital-asset question) severity **warning â†’ info**, retitled
    "defaulting to No", message reworded to the confirm-nudge. Unanswered now DEFAULTS to No on the header
    (the No box prints); No is a valid answer so the required question is still answered (matches TaxWise/Lacerte).
  - **`load_1040_intdiv_qdcgt.py`** â€” `D_SCHB_001` severity **error â†’ info**, condition widened to
    `part_iii_required AND (foreign_account_yes is NULL OR foreign_trust_yes is NULL)` so it now covers BOTH
    7a-1 (foreign account) AND line 8 (foreign trust) â€” the note always said it should, but the tts code only
    checked 7a-1 (fixed tts-side too). `R-SB-05` description updated: "the face never guesses" â†’ "unanswered
    7a-1 / line 8 DEFAULT to No; D_SCHB_001 (info) reminds to confirm."
- **Both integrity gates GREEN** (`check_spine_integrity.py` all clean, no dup/uncited; `check_intdiv_integrity.py`
  ALL CHECKS PASS â€” counts unchanged: spine 44 rules/91 facts/16 diags/32 scenarios; SCH_B 5/6/7/6). No new
  facts/rules/lines/diagnostics â€” pure severity/message/condition edits on existing entries.
- Seeded RS Supabase (`ylqaejdqwuvwpglxnpgv`, idempotent) â†’ re-exported `/api/forms/lookup/1040/export/` +
  `/api/forms/lookup/SCH_B/export/` â†’ overwrote tts `server/specs/1040_spine_spec.json` + `sch_b_spec.json`
  (semantic diff verified: ONLY the two diagnostics + R-SB-05 description changed, zero drift).
- tts side: render defaults (digital-asset + 7a-1/8 null â†’ No box), UI default-No YELLOW selects, `rules_1040.py`
  / `rules_schb.py` severities synced, tests updated. tts DiagnosticRule rows re-seed on the next Render deploy
  (build.sh idempotent seed_rules) â€” standard for any diagnostic change.

---

## 2026-06-30 â€” 1040_RETIREMENT: SSA withholding / Medicare / Railroad amendment SEEDED + EXPORTED (Ken go-ahead)
- Part of Ken's Bach-return UX batch (item 1). Ken greenlit the seed in-session. Amended `load_1040_retirement.py`:
  **+4 facts** (`ssa_fed_withheld`â†’25b, `ssa_medicare_premiums`, `ssa_medicare_destination` schedule_a|sehi,
  `ssa_is_railroad` RRB-1099 SSEB metadata), **+2 rules** (`R-RET-25B-SS` extends the 25b roster; `R-RET-MEDICARE`
  routes Medicare â†’ Sch A line 1 (Pub 502) OR SEHI Sch 1 L17 single-proprietor (Form 7206)), **+D_RET_009** RED
  (Medicare-as-SEHI with multiple businesses or Marketplace/PTC â†’ verify manually), **+2 scenarios** (RET-WH-1,
  RET-MED-1), **+2 flow assertions** (FA-1040-RET-09/10), **+3 rule_links**, **+2 authority sources**
  (`IRS_2025_PUB502`, `IRS_2025_F7206_INSTR`, both verbatim-verified 2026-06-30 against the live IRS text).
- **LAW VERIFIED 2026-06-30** against primary IRS sources (NOT memory â€” a WebFetch summary first gave a WRONG
  "Medicare not deductible" answer; re-fetched the actual pubs): i1040 line 25b (SSA-1099 box 6 / RRB-1099 box 10
  â†’ 25b); Pub 502 (Part B/D premiums ARE deductible medical; Part A if voluntarily enrolled); Form 7206 instr
  (Medicare premiums qualify as SEHI, capped at net SE profit, not for employer-subsidized months); Pub 915
  (RRB-1099 SSEB Tier 1 pools identically into box-5 â†’ 6a/6b).
- `check_retirement_integrity.py` â†’ **ALL CHECKS PASS** (independent math intact; unique ids; all rules cited).
  Counts: 1040_RETIREMENT 39 facts / 13 rules / 26 lines / 9 diagnostics / 22 scenarios / 18 links; FA 335 total.
- Seeded RS Supabase (`ylqaejdqwuvwpglxnpgv`, idempotent) â†’ re-exported `/api/forms/lookup/1040_RETIREMENT/export/`
  â†’ overwrote tts `server/specs/retirement_spec.json` (verified the 4 facts + 2 rules + D_RET_009 present).
- **NEXT (tts build):** Taxpayer model fields (+migration) â†’ compute (25b += SSA WH; Medicare â†’ Sch A L1 / SEHI
  single-proprietor) â†’ render (SSA vs RRB worksheet label) â†’ React SocialSecuritySection inputs + railroad
  checkbox + Medicare destination select â†’ `rules_retirement.py` D_RET_009 â†’ 2 flow assertions â†’ tests.

---

## 2026-06-29 â€” 1040_RETIREMENT: SS LUMP-SUM amendment SEEDED + EXPORTED (Ken go-ahead) â€” unit complete in tts
- Ken gave the in-session **"seed now, then build"** go-ahead. Ran `load_1040_retirement` against RS's own
  Supabase (`ylqaejdqwuvwpglxnpgv`) â€” idempotent (`update_or_create`); 1040_RETIREMENT now 35 facts / 11 rules /
  26 lines / 8 diagnostics / 20 scenarios / 15 links; FlowAssertions 333 total. DB totals: 74 forms / 1666 facts /
  637 rules / 419 diagnostics. Both integrity gates still report "all rules have authority links."
- Re-exported the deployed lookup endpoint (`/api/forms/lookup/1040_RETIREMENT/export/`) â†’ overwrote the canonical
  tts `server/specs/retirement_spec.json` (now carries the `lse_*` facts/rules/lines + D_RET_008 + the LSE-1/LSE-2
  tests). Verified lse_ws2_21 / lse_ws4_21 / ss_lump_sum_election / R-RET-LSE-WS4 present.
- tts side: re-seeded `1040_RETIREMENT` (added the lse_ws2_21/lse_ws4_21 pseudo-rows to the hardcoded
  `seed_1040_retirement.py`) and built the RENDER + INPUT + DB-test legs. **tts unit COMPLETE â€” tag
  `1040-ss-lumpsum-complete`.**
- STILL OPEN (RS hygiene): re-seed `load_4797` on the next RS deploy (covers both the 6252 + 8824 amendments; the
  deployed RS DB still has D_4797_003/004 active). The lump-sum amendment is now seeded; the 4797 one is not.

---

## 2026-06-28 â€” 1040_RETIREMENT amendment: SS LUMP-SUM ELECTION (Pub 915 WS2+WS4) â€” SPEC + MATH GATE GREEN (seed pending Ken go-ahead)
- **Retiree-hardening cluster, item 1 (D_RET_004).** Ken-directed (tts AskUserQuestion: chose D_RET_004 first +
  the EXPLICIT-TOGGLE election behavior, irrevocable-without-IRS-consent). Amended `load_1040_retirement.py`:
  the Pub 915 Lump-Sum Election is now COMPUTED, no longer the blanket RED-defer.
- **Added to 1040_RETIREMENT:** new authority source `IRS_2025_PUB915` (verbatim Worksheets 1/2/4 + the
  Terry Jackson worked example, `requires_human_review=True`); facts `ss_lump_sum_election` (toggle) + 9
  `lse_*` per-earlier-year facts; rules `R-RET-LSE-WS2` / `R-RET-LSE-WS4` / `R-RET-LSE-ELECT`; lines
  `lse_ws2_21` / `lse_ws4_21`; **D_RET_004 repurposed** (blanket RED â†’ no-silent-gap "earlier-year data
  missing" guard) + new **D_RET_008** (WS1-vs-WS4 comparison/savings, severity adapts tts-side); scenarios
  LSE-1 (Terry, election 2,500 < regular 3,000 â†’ beneficial) + LSE-2 (high earlier-year income â†’ WS4 4,200 >
  WS1 3,000 â†’ not beneficial); `FA-1040-RET-08`.
- **Counts now:** 1040_RETIREMENT 35 facts / 11 rules / 26 lines / 8 diagnostics / 20 scenarios / 15 links;
  flow assertions 8. `check_retirement_integrity.py` extended with an INDEPENDENT WS2/WS4 transcription
  (`_ss_tiers`/`ws2_additional`/`ws4_lse`) + LSE-1/LSE-2 checks + load-bearing benefit pins â†’ **ALL CHECKS PASS**.
- LAW VERIFIED 2026-06-28 vs the actual **Pub 915 (2025) PDF** (pages 10-19, pymupdf dump): Worksheets 1/2/4
  + the Lump-Sum Election method + the filled-in Terry example (reconciles to the dollar).
- **Method:** WS2 (per earlier year, post-1993) refigures that year's taxable benefits WITH the lump-sum
  portion added (L1 = earlier-year box5 + lump-for-year), subtracts the previously-reported taxable benefits
  (already inside AGI), â†’ additional taxable benefits (L21). WS4 re-runs the 2025 worksheet with box5 reduced
  by Î£(pre-2025 lump sums), then adds Î£ WS2 L21. Elect (6b = WS4 L21, check 1040 box 6c) only when the toggle
  is on; D_RET_008 surfaces whether it beats WS1. WS3 (pre-1994) RED-deferred (vanishingly rare).
- **READY_TO_SEED stays True** (form already approved+seeded 2026-06-11). The new lump-sum content is NOT yet
  seeded to the RS DB nor re-exported to `tts/server/specs/retirement_spec.json` â€” **pending Ken's in-session
  seed go-ahead** (he approved the substance; this is the formal flip-equivalent for the amendment).
- **NEXT (tts):** build the unit â€” `SocialSecurityLumpSum` model + `ss_lump_sum_election` on Taxpayer (migration)
  â†’ `compute_ss_lumpsum.py` (WS2/WS4, supersede 6b) â†’ render statement + 1040 box 6c â†’ input/serializer/CRUD/React
  â†’ `rules_retirement.py` D_RET_004 rewrite + D_RET_008 â†’ flow assertion â†’ tests (LSE-1/LSE-2). D_RET_005
  (IRA-deductionâ†”SS circular) + D_8606_NO_YEAREND remain the other two cluster items.

---

## 2026-06-28 â€” FORM 8824 (Like-Kind Exchanges + Â§1043) â€” SPEC AUTHORED + INTEGRITY GREEN + SEEDED âœ… (Ken approved)
- **Ken chose (tts AskUserQuestion): "Full incl. Part IV + computed recapture"** â€” the WHOLE Form 8824.
  New loader `load_8824.py` (form_number "8824", entity_types ['1040'], v1 â€” lookup was 404, brand-new
  form) in the modern pattern (module-level `compute_8824()` + `FORMS` + `FLOW_ASSERTIONS`) +
  `check_8824_integrity.py` (independent re-typed Â§1031 math).
- **Form 8824 v1: facts 41 / rules 7 / lines 35 / diagnostics 10 / scenarios 11 / links 14 / 9 flow
  assertions / 6 authority sources.** `check_8824_integrity.py` â†’ **ALL CHECKS PASS** (independently
  recomputed + cross-checked vs the loader AND the i8824 worked examples: Taylor Â§1245 L21 35000â†’4797
  L16 / L22 5000â†’4797 L5; Finley Â§1250 L21 30000, 25a 131250 / 25b 43750; loss âˆ’20000 deferred; Â§1043
  L37 130000; Â§1031(f) accel 60000). The gate caught one authored test-value error (T6 L19 50000â†’80000).
- **Model:** Part III Â§1031 â€” Â§1.1031(d)-2 symmetric liability netting (computed from components),
  L19 realized = L17âˆ’L18, L20 = max(0,min(L15,L19)), **COMPUTED** recapture L21 via Â§1245(b)(4)
  (min(min(depr,L19), L20+(L16âˆ’fmv1245))) + Â§1250(d)(4) (min(addl, max(L20, addlâˆ’fmv1250))) â†’ 4797
  line 16; L22 â†’ 4797 line 5 (business Â§1231 >1yr) / line 16 (ordinary) / Schedule D (capital);
  L23=L21+L22, L24 deferred (a LOSS defers in full, never deducted), L25=(L18+L23)âˆ’L15 + 25a/b/c
  proportional. Part II Â§1031(f) 2-year acceleration (prior-year L24 preparer-asserted). Part IV Â§1043
  L32/L34/L35â†’4797 L10/L37/L38 (L35 recapture preparer-asserted per i8824 worksheet method).
- **CLOSES the live Form 4797 D_4797_004 like-kind RED-defer** (L21â†’4797 L16, L22â†’4797 L5), same
  pattern the 6252 unit used to retire the 4797â†”6252 defer. (D_4797_004 closure = the tts COMPUTE/
  DIAGNOSTICS leg follow-up.)
- **v1 RED-defers (no silent gap):** multi-asset exchange (D_8824_007), Â§121 main-home combo
  (D_8824_008), personal property (D_8824_009 â€” post-2017 Â§1031 is real-property only). 45/180-day
  deferred-exchange deadline diagnostics (D_8824_001/002). **No year-keyed constants** (pure arithmetic
  â†’ TY2026 = TY2025 identical). OBBBA Â§1062 farmland-gain deferral (Form 1062) is a SEPARATE adjacent
  form, NOT part of 8824 â€” flagged to Ken, not built.
- LAW VERIFIED 2026-06-28 vs the actual **f8824.pdf (2025, both pages)** + **i8824.pdf (2025, 7 pages,
  incl. the Taylor/Finley liability-netting + Â§1245(b)(4)/Â§1250(d)(4) recapture + 25a/b/c examples)** +
  IRC Â§1031/Â§1031(f)/Â§1245(b)(4)/Â§1250(d)(4)/Â§1043 + Pub 544.
- **Ken APPROVED the review walk (2026-06-28)** â†’ flipped `READY_TO_SEED=True` â†’ seeded RS DB (TaxForms
  â†’ 74, FlowAssertions â†’ 332; "all rules cited") â†’ exported `tts/server/specs/form_8824_spec.json` (v1)
  + staged `flow_assertions_1040_8824_pending.json` (9 FA).
- **NEXT (tts):** build the 6 legs â€” COMPUTE (`compute_8824.py`, port of `m.compute_8824`, wired so
  L21â†’4797 L16 + L22â†’4797 L5 CLOSE D_4797_004) â†’ RENDER (f8824 PDF already in resources/2025; add
  manifest entry) â†’ DIAGNOSTICS (`rules_8824.py` 10 D_8824_*) â†’ INPUT â†’ ASSERTIONS (9 FA â†’ gate
  347â†’356). Reuse the 6252/4797 cross-form-feed pattern.
- **RS hygiene carryover (still open from 2026-06-28 6252 session):** `load_4797.py` amended +
  integrity-verified but the deployed RS was NOT re-seeded/re-exported for the 4797 amendments â€” do that
  on the next RS deploy alongside this 8824 seed (load_4797). (This 8824 seed DID write to the shared
  RS Supabase, so the 8824 export endpoint is live.)

### 2026-06-28 (later, tts 8824 COMPUTE leg) â€” load_4797.py AMENDED to CLOSE D_4797_004 (twin of the 6252 closure)
- `load_4797.py` `compute_4797` now accepts `like_kind_line5/16/10` feeds (Form 8824: recognized Â§1231
  gain â†’ Part I line 5; ordinary recapture/gain â†’ Part II line 16; Â§1043 ordinary â†’ line 10) and no
  longer RED-defers on `has_form_8824`. Marked `D_4797_004` + `f4797_has_form_8824` RETIRED (now
  supported); dropped `form_8824_like_kind` from FA-1040-4797-07's blocker list (only `form_4684_casualty`
  remains). `check_4797_integrity.py` â†’ **ALL CHECKS PASS** (11 scenarios; the additive feed params don't
  touch any existing scenario). 4684 casualty interplay still RED-defers.
- **Pending re-seed now covers BOTH the 6252 AND 8824 4797 amendments** â€” re-run `load_4797` on the next
  RS deploy (the deployed RS DB still has the old D_4797_003/004-active rows). The canonical tts
  `form_4797_spec.json` was mirrored by hand (D_4797_004 + fact retired-text). No other RS form touched.

## 2026-06-28 â€” FORM 4797 amended to CLOSE the 6252 RED-defer (tts Form 6252 compute leg)
- During the tts-tax-app Form 6252 (Installment Sale Income) COMPUTE leg, **Ken chose "fully retire the
  flag"** (close the 4797â†”6252 RED-defer rather than keep `f4797_has_form_6252` as a manual escape hatch).
- **`load_4797.py` amended** (byte-for-byte twin of the tts `compute_4797`): `compute_4797` now accepts
  `installment_line4/10/15` feeds (Â§1231 â†’ Part I line 4; ordinary â†’ Part II line 10; ordinary recapture â†’
  Part II line 15) and no longer RED-defers on `has_form_6252`. Removed the `F4797-G2` (6252 â†’ RED-defer)
  scenario; dropped `form_6252_installment` from FA-1040-4797-07's blocker list; marked the `D_4797_003`
  diagnostic + `f4797_has_form_6252` fact RETIRED (now supported). 4684/8824 interplays still RED-defer.
- **`check_4797_integrity.py` â†’ ALL CHECKS PASS** (now 11 scenarios; the Â§1231 netting + 5-yr lookback +
  Â§1245/1250/1252/1254/1255 recapture re-verified). The independent recompute was untouched (existing
  scenarios pass no installment feeds â†’ unchanged).
- **NOT YET re-seeded to the RS Supabase / re-exported via the lookup endpoint** (the loader is the source of
  truth and is integrity-verified; the canonical tts `form_4797_spec.json` was mirrored by hand to match â€”
  F4797-G2 removed, D_4797_003 + fact retired-text). **Pending hygiene: re-seed `load_4797` + re-export on the
  next RS deploy** so the deployed RS DB matches the amended loader. No other RS form touched.

## 2026-06-27 â€” FORM 4797 (Sales of Business Property) â€” SPEC REWRITTEN + INTEGRITY GREEN + SEEDED âœ… (Ken approved)
- **Ken chose (tts AskUserQuestions): the full Form 4797, then "Broad v1"** (Parts I-IV, all five
  recapture sections). REWROTE `load_4797.py` from the old "first form for validation" BaseCommand
  draft to the modern pattern (module-level `compute_4797()` + `FORMS` + `FLOW_ASSERTIONS`), so
  `check_4797_integrity.py` can re-type the math. SHARED form â€” form_number "4797", entity_types
  ['1120S','1065','1120','1040'] PRESERVED.
- **Form 4797 v2: facts 25 / rules 6 / lines 34 / diagnostics 7 / scenarios 12 / links 12 / 7 flow
  assertions / 8 authority sources.** `check_4797_integrity.py` (independent re-typed recapture math)
  â†’ **ALL CHECKS PASS** (T1 Â§1245 all-ord 10000 / T2 excessâ†’Sch D 20000 / T5 unrecap Â§1250 100000 /
  T6 lookback L9 12000 L18b 38000 / T7 Â§1252 18000 / T8 Â§179 7000).
- **Broad-v1 math:** Â§1245 L25b = min(gain, depr); Â§1250 L26g = applic% Ã— min(gain, 26a add'l depr),
  unrecaptured Â§1250 = min(gain, depr) âˆ’ Â§1250-ord (â†’ Sch D worksheet, 25%, NOT a 4797 line); Â§1252/
  1254/1255 = min(gain, section amount) (applic% preparer-entered); Â§1231 netting + Â§1231(c) 5-yr
  lookback: L12 ord = min(L7,L8), L9 = max(0,L7âˆ’L8) â†’ Schedule D line 11; Part IV Â§179/Â§280F L35 â†’
  Schedule 1 line 4. Routing: L18b + Part IV â†’ Sch 1 L4; L9 â†’ Sch D L11; L18a â†’ Sch A L16 (v1=0).
- **Ken's 3 tax-law calls (approved in-session):** Â§1231 lookback = preparer-asserted fact (default 0);
  Â§1250 26a additional depreciation = preparer-entered (default 0 = post-1986 SL); Â§179/Â§280F â†’ Sch 1
  L4 + SE-nuance INFO diag (auto SE add-back RED-deferred).
- **v1 RED-defers (no silent gap):** Form 4684 casualty, Form 6252 installment, Form 8824 like-kind.
- Verified Part III structure line-by-line vs the real **f4797.pdf (182 fields)** + i4797 (the field-map
  COMMENTS were wrong: 25a/b=Â§1245, 26a-g=Â§1250, 27=Â§1252, 28=Â§1254, 29=Â§1255). Authority: IRC Â§1231/
  1245/1250/1252/1254/1255 + Â§1(h)(1)(E) + Â§179(d)(10)/Â§280F(b)(2), i4797, Pub 544.
- **SHARED-FORM SEEDING GOTCHA:** the export serves `order_by('-version').first()` = v2; the DB had TWO
  identical old-draft rows (v1+v2). Set FORM_VERSION=2 to update the SERVED row. update_or_create left
  the old draft's children (R001-R010 rules, prefix-less facts, D001-D005, lines 19/26/27, 6 old tests)
  alongside the new â†’ "uncited rules: 9". FIX: PURGED all v2 children then re-seeded clean â†’ "all rules
  cited". (Lesson: amending an existing draft form needs a child-purge, not just update_or_create.)
- **Ken APPROVED the review walk (2026-06-27)** â†’ flipped `READY_TO_SEED=True` â†’ seeded RS DB (TaxForms
  72, FlowAssertions 308â†’315) â†’ exported `tts/server/specs/form_4797_spec.json` (v2).
- **NEXT (tts):** build the 6 legs â€” COMPUTE (`compute_4797.py`, port of `m.compute_4797`, wired BEFORE
  Schedule D netting; unrecaptured Â§1250 â†’ the Topic-9 SDTW worksheet) â†’ RENDER â†’ DIAGNOSTICS â†’ INPUT â†’
  ASSERTIONS. Reuse the existing `Disposition` model (is_4797 flag) + `resolve_recapture_type`.

---

## 2026-06-26 â€” FORM 1116 (Foreign Tax Credit) â€” SPEC AUTHORED + INTEGRITY GREEN + SEEDED âœ… (Ken approved)
- **Ken chose (tts AskUserQuestions): FULL Form 1116, then "Tighter v1 â€” Passive-only".** New loader
  `load_1040_form_1116.py` (form_number `FORM_1116`) + `check_1116_integrity.py` (independent re-typed
  math gate, the 2210 precedent). RS endpoint was 404 (greenfield, locally authored).
- **FORM_1116: facts 19 / rules 5 / lines 32 / diagnostics 8 / scenarios 10 / links 8 / 7 flow
  assertions / 3 authority sources.** `check_1116_integrity.py` â†’ **ALL CHECKS PASS** (T1 election 250 /
  T2 MFJ 550 / T4 limit-binds 1361 cf 139 / T5 full-credit 1000 cf 0 / T8 L17<=0 â†’ 0 cf 200).
- **Two paths:** Path A â€” Â§904(j) election (all passive + payee-statement + foreign tax â‰¤ $300/$600 â†’
  credit = min(foreign tax, regular tax) â†’ Sch 3 L1, no carryover). Path B â€” full Passive Â§904
  limitation (Part I L7 deduction apportionment â†’ Part III L21 = L20 Ã— L17/L18 â†’ L24 = min(L14,L23) â†’
  Part IV L35 â†’ Sch 3 L1; carryforward = max(0, L14âˆ’L24)). L18 = 1040 line 15 + Sch 1-A line 37 (the
  SENIOR deduction only â€” verified i1116). L20 = 1040 L16 + Sch 2 L1z.
- **v1 RED-defers (8 diagnostics, no silent gap):** non-passive category, the above-exception QD
  adjustment (foreign QD+gain â‰¥ $20k OR TI > threshold), Form 2555 reduction, carryoverâ†’Schedule B
  (warn), TY2026 threshold re-verify (warn), election-over-ceiling.
- Verified line-by-line vs the real **f1116.pdf (created 9/16/25) + i1116.pdf (Dec 23 2025)**
  (`tts/server/specs/_1116_source_brief.md`). Authority: IRC Â§901/Â§904/Â§904(j), Reg Â§1.904(b)-1, Pub 514.
- Constants: Â§904(j) $300/$600 (statutory); adj-exception TI $394,600 MFJ / $197,300 other (2025
  verbatim; 2026 interim = Â§199A $403,500/$201,750, flagged D_1116_007); adj-exception gain ceiling
  $20,000 (regulatory).
- **Ken APPROVED the review walk (2026-06-26)** â†’ flipped `READY_TO_SEED=True` â†’ seeded the RS DB
  (TaxForms 72, FlowAssertions 308, all rules cited) â†’ exported `tts/server/specs/1116_spec.json`.
- **NEXT (tts):** build the SEED leg (Form1116 model + migration + CRUD + f1116 PDF/manifest) â†’
  compute â†’ render â†’ input â†’ diagnostics â†’ assertions. Target: Schedule 3 line 1 flips to computed.

---

## 2026-06-25 â€” FORM 5329 FULL (Parts Iâ€“IX) â€” SPEC AUTHORED + INTEGRITY GREEN â³ (NOT seeded â€” awaiting Ken's review)
- **Ken chose (tts AskUserQuestions): FULL Form 5329 (all Parts Iâ€“IX) + DUAL taxpayer/spouse.**
  Expanded the `F5329_*` blocks IN PLACE in `load_1040_retirement.py` (the loader already owns
  form_number "5329"; no 2nd loader â€” avoids double-ownership). Spec is **owner-agnostic** (one
  logical form); DUAL is a tts-side model concern.
- **5329 form now (was 3/3/4/1/3): facts 37 / rules 12 / lines 58 / diagnostics 4 / scenarios 10
  / links 14.** Added Parts II (edu/ABLE 10%), IIIâ€“VIII (excess contributions 6% of the smaller of
  total-excess or 12/31 value, prior-year carryforward chain), IX (excess accumulation / missed RMD
  â€” SECURE 2.0 10% window / 25% other). `R-5329-12` aggregates all parts â†’ Schedule 2 line 8
  (replacing the Part-I-only feeder). Widened the line-2 exception catalog **01â€“12+19 â†’ 01â€“23+99**
  (i5329 table, incl. SECURE 2.0 codes 20/22/23); `D_RET_006` flipped from ">12 unsupported" to a
  validity guard (out of 01â€“23/99); `RET-G5` fixture exception 13â†’25 (13 is now valid Â§457).
- **`check_retirement_integrity.py` extended** (`f5329_full` recomputes all 9 parts; F5329-T1..T10
  scenarios incl. capped-vs-uncapped, the 10%/25% split, the all-parts Sch 2 L8 sum; +3 load-bearing
  pins). **ALL CHECKS PASS.**
- Verified line-by-line vs the real **f5329.pdf + i5329.pdf** (2026-06-25;
  `tts/server/specs/_5329_full_source_brief.md`). Authority: IRC Â§Â§72(t)/4973/4974, SECURE 2.0 Â§302,
  Notices 2024-02/2024-55.
- **PENDING:** Ken's review walk â†’ then re-seed the RS DB (run `load_1040_retirement`) â†’ export
  `5329_spec.json` â†’ tts build legs. `READY_TO_SEED` is already True (retirement spec), so the gate
  here is DISCIPLINE: do not run the loader until Ken approves the 5329 expansion.

## 2026-06-25 â€” FORM 1040-X (Amended Returns) â€” APPROVED + SEEDED + EXPORTED âœ…
- **Ken APPROVED the W1-W6 review walk in-session** (W1 amend-in-place + dedicated as-filed
  baseline / W2 col-B = Câˆ’A / W3 refund-owe 17-23 / W4 confirm the deferrals â€” NOL/GBC
  carrybacks + superseding + multi-form cascades RED-defer / W5 year / W6 Part II required).
  Flipped `READY_TO_SEED=True` â†’ seeded RS DB (12 facts/12 rules/61 lines/8 diag/2 tests/6 FA)
  â†’ exported canonical `tts/server/specs/1040x_spec.json`. Integrity gate ALL PASS. RS `957a9d6`.
- tts compute leg built on the approved spec (compute_1040x + render_1040x + rules_1040x + 6
  FA-1040X merged); full 1040-X suite 343 passed; **tag `1040x-complete`**.

## 2026-06-25 â€” FORM 1040-X (Amended Returns) â€” AUTHORED (READY_TO_SEED=False) â¸ï¸
- **NEW spec `load_1040_form_1040x.py`** (remote-safe spec+scaffold pass; the tax-law
  delta-compute leg waits for Ken). Form 1040-X = a three-column A/B/C delta over a filed
  1040: Column A = original/as-filed (from a frozen `AsFiledBaseline` snapshot, tts side),
  Column C = correct (the amended 1040), Column B = net change (C âˆ’ A); recompute subtotals
  (3/5/8/11) + amended refund/owe (17-23) + Part II explanation.
- **12 facts / 12 rules / 61 lines / 8 diagnostics / 2 scenarios / 6 FA.** Line set verified
  against the ACTUAL Form 1040-X (Rev. December 2025) PDF â€” read directly from
  tts/resources/irs_forms/2025/f1040x.pdf (widget dump + text), NOT memory. RED-defers NOL
  carryback (D_1040X_001), GBC carryback (002), superseding (003), missing baseline (005),
  blank explanation (004), other-credit cascades (008).
- **`check_1040x_integrity.py`** â€” independent recompute (B=Câˆ’A + subtotals + refund/owe) re-
  derives both scenarios + structural checks (no dup ids, rule_links resolve, expected_outputs
  reference real lines, idâ‰¤20). **ALL CHECKS PASS.** The seed command correctly REFUSES
  (`READY_TO_SEED=False`). W1-W6 review-walk items in the loader docstring for Ken.
- **NOT seeded / NOT exported** â€” awaiting Ken's review (REVIEW_QUEUE.md). RS `4ba236c`.

---

## 2026-06-25 (later) â€” GA FORM 500 â€” page-5 line-number fix + HB 463 TY2026 constants âœ…
- **Amended `load_ga500_form_500.py` + `check_ga500_integrity.py`** (the spec was WRONG on the
  page-5 line numbers, verified vs the actual GA-DOR 2025 Form 500 PDF page 5). Corrected to the
  form face: **L42 = UET penalty, L43 = late-payment penalty, L44 = Interest, L45 = AMOUNT DUE
  (= L29 + Î£ lines 32-44), L46 = REFUND (= max(0, L30 âˆ’ Î£ lines 31-44))**; added the 10 gift
  check-offs (L32-41) + late-penalty/interest facts. The prior spec mis-keyed UET as "44" and
  never modeled L45. Extended `recompute()` to cover L28-46 + 2 new scenarios (T13 refund / T14
  amount-due). Integrity gate ALL PASS (**14 scenarios**). RS `14e4410`.
- **HB 463 TY2026 standard deduction corrected** (was still $12k/$24k for 2026): GA_STD_DED_MFJ
  [2026] 24000â†’30000, GA_STD_DED_OTHER[2026] 12000â†’15000 (loader + integrity). Dependent
  exemption $5,000 was already right. **Effective-year CONFIRMED WITH KEN** (sources conflicted:
  BIP Wealth/BDO = TY2026 vs GBPI = TY2027; Ken chose TY2026 â€” verify vs the bill text later).
  Scenario T11 recomputed (tax 2994). RS `fd9ebc9`.
- **Re-seeded RS DB** (deleted a stale renamed-T11 orphan first; `manage.py shell`) â†’ **re-exported
  the canonical `tts/server/specs/500_spec.json`** (77 facts / 21 rules / 89 lines / 12 diag / 14
  tests). Deployed export reflects it (same Supabase RS DB). Implemented on the tts side (seed/
  compute/render/diagnostics); GA-500 tag `ga500-complete`.

---

## 2026-06-25 â€” GA FORM 500 (Georgia Individual Income Tax) â€” AUTHORED + SEEDED + EXPORTED âœ…
- NEW form (Ken's direction after Form 8615 completion). **No prior RS spec** â€” `lookup/500`,
  `GA_500`, `GA500` all â†’ 404. The **FIRST STATE individual spec** (all prior specs federal).
- **Verified against the GA-DOR 2025 Form 500 (Rev. 07/09/25) + 2025 IT-511 booklet (extracted
  from the actual PDFs, read directly) + O.C.G.A. Title 48 Ch. 7 + HB 111 (TY2025 rate) + HB 463
  "Georgia Economic Growth and Tax Relief Act of 2026" (TY2026), NOT memory.** Georgia Form 500:
  federal AGI (1040 L11) â†’ Schedule 1 GA additions/subtractions (the retirement income exclusion
  is the center of gravity) â†’ standard/itemized deduction â†’ dependent exemption â†’ GA NOL (Sch 4,
  80% limit) â†’ flat tax â†’ credits â†’ withholding â†’ refund/due.
- **v1 scope LOCKED (Ken, 4 AskUserQuestion decisions 2026-06-25 â€” MAXIMAL):** (1) resident **+
  part-year/nonresident** (Schedule 3 proration); (2) **both** retirement exclusions (standard RIE
  + military); (3) **compute Schedule 4 GA NOL** (Part I/II + 80% limit); (4) credits direct-entry
  **+ compute the Low Income Credit + IND-CR 202 child-care** (50% of the federal Â§21). The
  Â§168(k)/Â§179/OBBBA depreciation difference (Sch 1 L3/L11) = preparer DIRECT-ENTRY in v1 (GA
  conforms to the IRC as of 1/1/2025, NOT OBBBA; engine integration later â€” W1). RED-defers the UET
  penalty + the multi-year NOL carryover application.
- **CONSTANTS verified:** rate 5.19% (2025, HB 111) / 4.99% (2026, HB 463); std ded $24,000 MFJ /
  $12,000 else (no age-65/blind add-on, no personal exemption â€” HB 1437); dependent exemption
  $4,000 (2025) / **$5,000 (2026, HB 463 eff. TY2026)**; retirement exclusion $35,000 (62-64/
  disabled) / $65,000 (65+), â‰¤$5,000 earned; military $17,500 base â†’ $35,000; LIC table
  $26/$20/$14/$8/$5 by FAGI bracket (< $20,000). Std-ded + retirement-exclusion bumps start 2027.
- `load_ga500_form_500.py` = **75 facts / 20 rules / 76 lines / 12 diagnostics / 12 tests / 21
  rule-links / 12 FA / 4 sources** (+ ref IRS_2025_1040_FORM). The project's largest spec.
  `check_ga500_integrity.py` **ALL CHECKS PASS** â€” constants (2 yrs) + helpers + the LIC table +
  all 12 scenarios (the Form 500 assembly: Sch 1 / RIE std+military / deduction / Sch 3 / NOL 80% /
  flat tax / LIC / child-care) re-derived independently; loader + gate share no math. Full source
  brief: `tts-tax-app/server/specs/_ga500_source_brief.md`.
- **READY_TO_SEED = True** â€” Ken **APPROVED the review walk in-session 2026-06-25** ("Approve as
  drafted â€” seed + export"; W1-W6 all blessed). **SEEDED** (`manage.py load_ga500_form_500` â†’
  Created 500; 75 facts / 20 rules / 21 authority links / 76 lines / 12 diagnostics / 12 tests /
  12 FA / 5 sources). **EXPORTED** the canonical spec â†’ `tts-tax-app/server/specs/500_spec.json`
  (82 KB; facts 75 / rules 20 / line_map 76 / diagnostics 12 / tests 12) + the 12 staged
  `flow_assertions_1040_ga500_pending.json` (FA-GA500-01..12). **NEXT: the tts-tax-app BUILD legs
  (seed model/migration â†’ compute â†’ render â†’ input â†’ diagnostics â†’ assertions) â€” GA 500 attaches
  to the child 1040 via the `state_returns` FK (the GA-600S precedent).**

---

## 2026-06-24 â€” FORM 8615 (Kiddie Tax Â§1(g)) â€” DRAFTED + GATE PASS â€” AWAITING KEN'S REVIEW WALK â³
- NEW form (Ken chose it after 8829, from a Phase-0 finding that the whole SPRINT_SCOPE
  NEXT-UP federal backlog is already built). **No prior RS spec** â€” `lookup/8615`,
  `FORM_8615`, `1040_8615` all â†’ 404.
- **Verified against i8615 (2025) + f8615 (read directly) + IRC Â§1(g) + Â§63(c)(5)(A) +
  Â§1(h); 2026 constants from Rev. Proc. 2025-32 Â§3.02/Â§3.18 (read the PDF directly), NOT
  memory.** The kiddie tax: Part I net unearned income = min(unearned âˆ’ $2,700, taxable
  income); Part II tentative tax at the PARENT's rate (tax on net unearned + parent TI +
  other children's net unearned âˆ’ the parent's tax, allocated by L5 Ã· (L5+L7)); Part III
  child's tax = LARGER of (parent-rate share + child-rate tax on the rest) vs (child-rate
  tax on all) â†’ child's 1040 line 16.
- **Scope LOCKED (Ken, 2 AskUserQuestion decisions 2026-06-24):** (1) parent data =
  preparer-asserted facts on the child's return (no parent-return link in v1); (2) cap-gains
  = FULL QDCGT reuse (`compute_qdcgt_worksheet` + i8615 Line 5 worksheets, parent/child
  `ordinary_tax_fn`), RED-defer ONLY Â§1250/28% SDTW (+ Schedule J + Form 8814 election).
- **CONSTANTS verified:** Â§63(c)(5)(A) base = $1,350 BOTH 2025+2026 (unchanged) â†’ line 2 /
  threshold = $2,700 both years. Rate schedules / QDCGT breakpoints REUSE the existing
  year-keyed constants (lines 9/15/17 tax-at-rate values are the reuse; the spec owns the
  Â§1(g) assembly).
- `load_1040_form_8615.py` = **30 facts / 11 rules / 18 lines / 7 diagnostics / 8 tests /
  16 rule-links / 9 FA**. `check_8615_integrity.py` **ALL CHECKS PASS** (the Â§1(g) assembly
  + constants + helpers re-derived independently; loader + gate share no math). Full source
  brief: `tts-tax-app/server/specs/_8615_source_brief.md`.
- **READY_TO_SEED = False** â€” the loader REFUSES to seed (zero DB writes) until Ken's
  in-session review walk (W1 the Â§1(g) assembly + max(L16,L17); W2 the preparer-asserted
  parent data; W3 the QDCGT-in/SDTW-out boundary; W4 the Line 5 worksheet posture [spec the
  principle, transcribe the WS lines at compute]; W5 the L13 precision; W6 the constants).
  **NEXT: Ken reviews â†’ flip READY_TO_SEED â†’ seed â†’ deploy export â†’ canonical
  `8615_spec.json` + 9 staged FA.**

---

## 2026-06-24 â€” FORM 8829 (Business Use of Home) â€” AUTHORED + SEEDED + EXPORTED âœ…
- NEW form after the quick-wins bundle (Ken chose Form 8829 home office, then "BROADER:
  build the Schedule A split"). **No prior RS spec** â€” `lookup/8829/export/` â†’ 404.
- **Verified against the actual 2025 f8829.pdf (read directly) + i8829 (Rev. Mar 4 2026)
  + IRC Â§280A(c)(5) + Â§168/Pub 946, NOT memory.** The actual-expense home-office engine:
  Part I business % (area + daycare hours-of-use) â†’ the Â§280A(c)(5) gross-income limitation
  in 3 ordered tiers (deductible-anyway 9-14 â†’ operating 16-27 â†’ casualty+depreciation
  29-33, each limited to the income remaining; depreciation last â†’ carries over first) â†’
  line 36 â†’ Schedule C line 30; Part III 39-yr nonresidential mid-month SL depreciation
  (Jan 2.461%â€¦Dec 0.107% first year, 2.564% subsequent); Part IV carryover.
- **Scope LOCKED (Ken, AskUserQuestion "Approve as drafted"):** v1 COMPUTES the RE-tax
  SALT split (lines 11/17) reusing `compute_schedule_a.salt_line5e` (the OBBBA $40k cap +
  $500k-MAGI 30% phasedown) incl. the >$500k circular MAGIâ†”home-officeâ†”AGI iteration
  (W4 = fixed-point loop). The MORTGAGE Pub-936 split (10/16) stays a preparer fact for
  itemizers (W3 â€” matches Schedule A; the standard-deduction path is computed). RED-defers
  line-35 â†’ Form 4684 + the multi-business line-36 allocation (W5).
- `load_1040_form_8829.py` (the `load_1040_form_6251` template): **47 facts / 13 rules /
  44 lines / 8 diagnostics / 11 scenarios / 9 FA / 20 authority links / 4 sources** (+ ref
  IRS_2025_1040_FORM). `check_8829_integrity.py` math gate **ALL CHECKS PASS** â€” the
  depreciation table (12 months + subsequent) + daycare + SALT constants + helpers + all
  11 scenarios re-derived independently (caught + fixed 2 self-authored scenario errors:
  itemizer line 11/17 are col (a) pre-allocated, not col (b) Ã— business %). RS `b933b6e`.
- **Ken APPROVED the review walk in-session ("Approve as drafted")** â€” W1 Â§280A tier
  ordering; W2 39-yr nonresidential mid-month depreciation; W3 itemizer-mortgage-split-as-
  input; W4 the MAGI fixed-point loop; W5 casualty/4684; W6 constants reused from Sch A.
  FLIPPED `READY_TO_SEED` â†’ seeded (RS DB: Created 8829) â†’ deployed export verified
  (`lookup/8829/export/` HTTP 200; 47/13/44/8/11) â†’ canonical `server/specs/8829_spec.json`
  committed to tts-tax-app + 9 FA staged in `flow_assertions_1040_8829_pending.json`.
- **Next (tts-tax-app): the 6 build legs (seed â†’ compute â†’ render â†’ input â†’ diagnostics â†’
  assertions).** Build leg 1 = model fields (Form8829 per Schedule C) + migration + manifest
  f8829 + download PDF + seed_8829 + serializer.

## 2026-06-24 â€” FORM_2441 â€” claims_dependent_care claim gate (amend; NOT re-seeded yet)
- tts-tax-app quick-win (Ken chose "amend spec + gate compute"): the per-Dependent
  `claims_dependent_care` checkbox is now the AUTHORITATIVE claim election for the Â§21
  credit. Previously R-2441-QUALIFYING counted qualifying persons by `care_expenses > 0 +
  (under-13 OR disabled)` only â€” a qualifying-but-unclaimed dependent computed a credit.
- **Loader amended** (`specs/management/commands/load_1040_form_2441.py`): R-2441-QUALIFYING
  formula/description/inputs now gate on `claims_dependent_care`; NEW `claims_dependent_care`
  fact (boolean, sort 6); NEW diagnostic **D_2441_007** (info) â€” a qualifying dependent with
  care expenses but not claimed â†’ no credit computed (no silent gap). check_2441_integrity.py
  unaffected (it recomputes the worksheet from `qualifying_count` as input; the gate is upstream).
- **NOT re-seeded / re-exported** this session (no local RS DB run from the tts-tax-app session).
  The canonical `form_2441_spec.json` in tts-tax-app was hand-amended to match the loader and is
  green there (flow gate 282â†’283, FA-1040-2441-07; 2441 tests 36/36). **TODO next RS deploy:**
  run `load_1040_form_2441` + `check_2441_integrity.py`, re-export `lookup/FORM_2441/export/`,
  and diff against the tts-tax-app canonical spec to confirm zero drift.

## 2026-06-23 â€” FORM 6251 (Alternative Minimum Tax) â€” AUTHORED + SEEDED + EXPORTED âœ…
- Next Tier-2 unit after 8995-A (Ken chose the AMT engine). **No prior RS spec** â€”
  `lookup/6251/export/` returned 404 (a genuinely NEW form, not a re-author).
- **Scope LOCKED (Ken, AskUserQuestion): "common-case engine"** â€” v1 computes the SALT/
  std-deduction add-back (2a) / PAB (2g) / AMT depreciation (2l) / refund (2b) / exemption +
  phaseout / Part II 26-28% TMT / Part III AMT cap-gains â†’ AMT = max(0, TMT âˆ’ regular tax)
  â†’ Schedule 2 line 2. RED-defers ISO (2i), QSBS (2h), NOL (2e/2f), estates/trusts (2j), the
  exotic preferences (2c/2d/2k/2m/2n/2o-2t/3), and the AMT FTC (line 8).
- **Verified against the actual 2025 f6251.pdf (read directly via pymupdf â€” Part I 1a-4 incl.
  all 2a-2t, Part II 5-11, Part III 12-40 AMT cap-gains worksheet) + i6251 + IRC Â§Â§55-59 +
  OBBBA Â§70107, NOT memory.** AMTI base (Ken-confirmed): regular taxable income + std-deduction/
  SALT add-back + senior-deduction add-back; QBI retained. Constants both years: 2025
  exemption 88,100/137,000/68,500 @ phaseout 626,350/1,252,700 Ã— 25%; **2026 OBBBA**
  90,100/140,200/70,100 @ **500,000/1,000,000 Ã— 50%** (the phaseout reversion + rate doubling).
- `load_1040_form_6251.py` (the `load_1040_form_8995a` template): **25 facts / 14 rules /
  38 lines / 8 diagnostics (6 RED-defer D_6251_* + AMT-applies info + Part III basis-diff warn) /
  10 scenarios / 9 FA + 25 authority links**. `check_6251_integrity.py` math gate **ALL CHECKS
  PASS** â€” constants (both years Ã— 3 statuses) + helpers + all 10 scenarios re-derived
  independently (caught + fixed 4 scenario arithmetic errors). RS `b8d3333` (author) + the flip.
- **Ken APPROVED the review walk in-session ("approve and seed")** â€” W1-W6 blessed as drafted
  (W1 AMTI base; W2 the 2026 OBBBA $90,100/$140,200/$70,100 + $500k/$1M @ 50%; W3 RED-defer scope;
  W4 Part III reuse; W5 line-10 no-Schedule-J; W6 D_AMT_DEFER narrowing). FLIPPED `READY_TO_SEED`
  â†’ seeded (RS DB +1 form `6251`; 25/14/38/8/10/9 + 25 links + 1 topic + 6 sources) â†’ deployed
  export verified (`lookup/6251/export/` HTTP 200, counts + OBBBA $500k + all 8 D_6251_*) â†’
  canonical `server/specs/6251_spec.json` committed + 9 FA staged in
  `flow_assertions_1040_6251_pending.json`.
- **Next (tts-tax-app): the 6 build legs (seed â†’ compute â†’ render â†’ input â†’ diagnostics â†’
  assertions).**

## 2026-06-23 â€” FORM 8995-A (above-threshold QBI) â€” AUTHORED + SEEDED + EXPORTED âœ…
- **Ken APPROVED the review walk in-session ("Approve & seed")** â€” the next Tier-2 big-ticket
  item after 8582 per-activity (Ken chose 8995-A over the Form 6251 AMT engine). The full
  above-Â§199A-threshold QBI computation: W-2/UBIA limit, SSTB phase-in, aggregation, loss netting.
- **Verified against the actual 2025 f8995a.pdf (read directly â€” Parts I-IV exact, 2 pages/111
  widgets) + i8995a (12pp, Schedule A/B/C mechanics), NOT memory.** Locked scope (AskUserQuestion
  2026-06-23): **Parts I-IV + Schedule A (SSTB applicable %) + Schedule B (FULL aggregation engine,
  Ken's choice) + Schedule C (per-business loss netting)** = IN; **Schedule D (patron reduction L14
  + DPAD Â§199A(g) L38)** = RED-deferred (D_8995A_001/002; ag/hort-coop patrons rare).
- **NEW loader `load_1040_form_8995a.py`** RE-AUTHORS the thin hand-authored `8995A` draft (20
  facts/6 rules/15 mismatched lines) into the real face: **21 facts / 11 rules / 51 lines /
  7 diagnostics / 10 worked scenarios / 9 FA** (FA-1040-8995A-01..09). `_retire_stale_8995a`
  dropped 43 stale draft rows on seed. Standalone loader (touches only 8995A + 1 new topic
  `qbi_above_threshold` + 1 new source `IRS_2025_8995A_FORM` + 3 excerpts on existing
  `IRS_2025_8995A_INSTR`); does NOT touch the simplified 8995 or anything else.
- **Core mechanics (Ken-verified, W1-W7):** (W1) Schedule A applicable% = clamp((ceilingâˆ’TI)/range,
  0,1) â€” the fraction RETAINED, reduces QBI/W-2/UBIA, stacks with the Part III phase-in;
  (W2) Schedule C apportions the total QB loss (current + prior carryforward) pro-rata by QBI across
  positive businesses, adjusted QBI â‰¤0 â‡’ that biz's W-2/UBIA = 0, net negative â†’ line-6 carryforward;
  (W3) Schedule B full aggregation â€” combine QBI/W-2/UBIA, ownership/factors PREPARER-ASSERTED,
  none-SSTB ENFORCED (D_8995A_007 error); (W4) patron/DPAD RED-deferred; (W5) line-34 net cap gain =
  qual div + Sch D min(15,16), IDENTICAL to simplified-8995 L12; (W6) phase-in range $50k/$100k MFJ
  STATUTORY NON-INDEXED, ceiling = threshold + range (year-keyed via threshold); (W7) no public
  fillable Schedule A/B/C PDF (irs.gov f8995a.pdf = 2-pp main form only) â†’ schedules authored at the
  COMPUTATIONAL level, exact PDF widget layout verified at the render leg.
- `check_8995a_integrity.py` INDEPENDENT re-derivation (own constants, no shared math) â†’ **ALL 10
  SCENARIOS PASS** (T1 non-SSTB above ceiling/wage binds; T2 in-band phase-in relief 10kâ†’15k;
  T3 SSTB applicable% 50%; T4 SSTB above ceilingâ†’$0; T5 loss netting 100k+(âˆ’40k)â†’60k; T6 income
  limit binds; T7 REIT/PTP only; T8 aggregation 9kâ†’20k; T9 patron RED; T10 TY2026 year-keying).
  Constants cross-checked cell-by-cell + RS varchar(20) id-length guard + line-uniqueness + text pins.
- **Deployed export verified HTTP 200** (`lookup/8995A/export/`: 21/11/51/7/10, all 11 rules + 7
  diagnostics + lines 26/39/A-APPLPCT/SC-1C present). Committed tts-tax-app canonical
  `server/specs/8995a_spec.json` + **9 FA staged** in `flow_assertions_1040_8995a_pending.json`
  (active 1040 gate holds at **264** until the assertions build leg). RS commit `b1d7853` (pushed);
  tts `d737e08` (pushed).
- **NEXT (tts-tax-app build legs):** leg 1 seed (per-business `w2_wages`/`ubia` on ScheduleC/F + 
  `w2_wages`/`ubia`/`is_sstb` on ScheduleK1 â€” NO such fields exist today; aggregation grouping model +
  Schedule B eligibility facts; additive migration to the shared DB; f8995a manifest; 8995A form def
  seed; serializer CRUD) â†’ compute (`compute_8995a`, replace the D_8995_001 above-threshold blank) â†’
  render (un-stub f8995a_2025.py + Schedules A/B/C) â†’ input â†’ diagnostics (narrow D_8995_001; add the
  7 D_8995A_*) â†’ assertions (merge 9 FA, gate 264â†’273, tag `1040-8995a-complete`).

## 2026-06-23 â€” FORM 8582 PER-ACTIVITY (Parts IV-VIII) â€” AMENDED + SEEDED + EXPORTED âœ…
- **Ken APPROVED the review walk in-session ("Approve â€” flip & seed")** â€” the full Â§469 per-activity
  allocation, extending the 2026-06-14 aggregate Part I-III v1 (tag `1040-schedule-e-8582-complete`).
  **Closes the STATUS Tier-2 "Form 8582 fed by K-1 / Sch C-E-F" gap** (passive K-1/Sch-C/Sch-F losses were
  RED-deferred by `d_k1_passive_loss`; this routes them through 8582's Part V "other passive" bucket).
- **Verified against the actual 2025 f8582.pdf (3 pages, 205 widgets â€” Parts IV-IX are FILED, not
  "keep for your records") + i8582 (2025), NOT memory.** Locked scope (AskUserQuestion): **Parts IV-VIII**
  (Part IX = losses on 2+ forms / 28%-rate / Â§1231 RED-deferred â€” the triggers already defer upstream in
  the K-1 router); **all four activity types feed Part V** (non-active rental + passive K-1 + passive
  Sch C + passive Sch F).
- `load_1040_schedule_e.py` amended ADDITIVELY (FORM_8582 only): **+6 rules** (R-8582-WS-NET / -ALLOC-VI /
  -ALLOC-VII / -ALLOWED-VIII / -CARRYFWD / -MULTIFORM), **+1 fact** (`f8582_line_c`), **+6 lines**
  (C, P4-P8 descriptors), **+1 diagnostic** (`D_8582_MULTIFORM` RED), **+4 scenarios** (PA1/PA2/PA3 worked
  math + PG1 the RED), **+12 rule-links**, **+1 i8582 excerpt** (Parts IV-IX), **+3 FA** (FA-1040-8582-05/06/07).
  FORM_8582 now **18 facts / 12 rules / 23 lines / 7 diag / 11 tests / 20 links / 9 FA** (was 17/6/17/6/7/8/6).
- **Core mechanic (Ken-verified):** line C = (Part I line 3 loss) âˆ’ (Part II line 9) = total unallowed;
  Part VI allocates line 9 across active-rental losses by loss-ratio; Part VII allocates line C across the
  pool [Part VI col(d) + Part V col(e)] by loss-ratio (Î£ = line C); Part VIII allowed = activity loss âˆ’
  its unallowed â†’ its own schedule. Conservation: **Î£ allowed = line 11 (= line 9 + line 10)**.
- `check_schedule_e_8582_integrity.py` extended with an INDEPENDENT per-activity recompute (no shared
  loader math) â†’ **ALL CHECKS PASS** (PA1 .75/.25 split; PA2 income-offset; PA3 no-allowance + conservation).
- **NEW loader `--only FORM_8582` option** â†’ seeded SCOPED so SCHEDULE_E is untouched (protects the K-1
  router's page-2 spec + the FA-1040-SCHE-01 line-41 repoint). Seed: FORM_8582 Updated (18/12/23/7/11/20,
  7 FA scoped). **Deployed export verified HTTP 200** (`lookup/FORM_8582/export/`: 12 rules incl. the 6 new,
  D_8582_MULTIFORM, PA1/PA2/PA3/PG1). Committed tts-tax-app canonical `server/specs/form_8582_spec.json`
  (re-export) + **3 FA staged** in `flow_assertions_1040_sche_8582_pending.json`.
- **NEXT (tts-tax-app build legs):** seed (per-activity prior-unallowed model field on RentalProperty/
  ScheduleK1/ScheduleC/ScheduleF â€” migration) â†’ compute (extend `compute_8582.py` per-activity + feed
  Part V from K-1/C/F; allocate back; carryforward) â†’ render (f8582 field map Parts IV-VIII) â†’ input â†’
  diagnostics (RETIRE `d_k1_passive_loss`; add D_8582_MULTIFORM) â†’ assertions (merge the 3 FA) â†’
  tag `1040-8582-per-activity-complete`.

## 2026-06-22 â€” FORM 4562 Â§179 PRIOR-YEAR CARRYOVER (Part I L10/12/13) â€” AMENDED + SEEDED + EXPORTED âœ…
- **Ken APPROVED the review walk in-session ("Approve & seed")** â€” the verified L10-L13 wording off the
  2025 Form 4562 PDF; the Line 11 **Individuals** business-income definition; R014/R015 carryover rules;
  D014 proforma-continuity; the 3 instruction excerpts. Flipped `READY_TO_SEED â†’ True` â†’ math gate stayed
  green â†’ **seeded onto the EXISTING 4562 v1** (additive amendment): **facts 19â†’20, rules 10â†’12, lines
  24â†’26, diagnostics 8â†’9, tests 9â†’14**; entity_types **['1120S','1065','1120','1040'] UNTOUCHED**.
  **Deployed export verified HTTP 200** (`lookup/4562/export/`; L10/L11/L12/L13 present, L12 calc =
  `min(line_9 + line_10, line_11)`, R014/R015/D014/section_179_carryover_prior present). Committed
  tts-tax-app canonical `server/specs/form_4562_spec.json` (re-export) + **4 FA staged** in
  `flow_assertions_4562_section179_pending.json` (FA-4562-179-01..04).
- **WHY:** the 1040 proforma unit (Tier 1 Item 1) carries a prior-year Â§179 carryover forward
  (Taxpayer.sec_179_carryover_prior â†’ line 10), which must be consumed (line 12) and any remainder
  re-carried (line 13). The existing 4562 spec was SILENT on lines 10/13 and its line-12 description was
  WRONG ("smaller of line 9 or line 11"). Per the MANDATORY Rule Studio rule + "flag if the spec is silent,
  do not guess" â€” fetched the spec, found the gap, Ken chose **amend RS spec first, then build inline**
  (AskUserQuestion 2026-06-22). NEW loader `load_4562_section179_carryover.py` AMENDS additively (looks up
  the form, never recreates it).
- **LAW VERIFIED 2026-06-22 â€” NOT memory:** Form face `resources/irs_forms/2025/f4562.pdf` (pymupdf dump):
  L10 "Carryover of disallowed deduction from line 13 of your 2024 Form 4562"; L11 "Business income
  limitation. Enter the smaller of business income (not less than zero) or line 5"; L12 "Add lines 9 and
  10, but don't enter more than line 11"; L13 "Add lines 9 and 10, less line 12". Instructions
  (irs.gov/instructions/i4562) Line 11 **Individuals**: smaller of L5 or total taxable income from any
  actively-conducted trade/business + **all wages/salaries/tips (Form 1040 line 1a)**, computed without
  Â§179, the Â§164(f) Â½-SE-tax deduction, or any NOL; MFJ combine both spouses.
- **MATH GATE `check_4562_section179_integrity.py` ALL CHECKS PASS** â€” independent re-type of
  L12 = min(L9+L10, L11) / L13 = (L9+L10) âˆ’ L12 over 5 scenarios (fully-absorbed / income-limitedâ†’3k carry /
  zero-carryover regression / both-limitedâ†’25k carry / zero-incomeâ†’full carry) + carryover-conservation
  invariant (L12+L13 = L9+L10) + text-pins guarding against reverting L12 to the old wrong formula. Loader
  & gate share no math.
- **TWO BUILD-LEG decisions (downstream â€” do NOT change this spec):** (a) the line-11 v1 component scope
  for 1040 (recommend Sch C + Sch F net + W-2 wages 1040 L1a; flag K-1 active income / business Â§1231);
  (b) per-business allocation of a return-level carryover. Decide at the Â§179-consumption compute leg.
- **Next (tts-tax-app): the proforma build legs** â€” model/migration (Taxpayer.sec_179_carryover_prior +
  TaxReturn provenance pointer); Â§179 consumption compute+render (line 11 business-income limit + L12/L13 +
  per-business allocation, renderer.py:1748); 1040 roll-forward `_populate_*_from_prior_year`; UI;
  tests + merge the 4 FA. Design precedent: `_expand_4562` (the prior 4562 authoring) + `load_1040_schedule_f.py`.

## 2026-06-21 â€” SCHEDULE_J (1040 income averaging) â€” SEEDED + EXPORTED âœ…
- **Ken APPROVED the review walk in-session ("Approve & seed now")** â€” the 4 requires_human_review walk
  items ruled, ALL matching the authored spec (no edits): Q-A line-4 SDTW REDUCES the current-year Sch D
  net cap gain by 2b (unrecap Â§1250 by 2c), floored at 0; Q-B line 6 = round_half_up(2a/3); Q-C SDTW
  ordinary lines 44/46 (instr's 34/36 & 42/44 are stale); Q-D D_SJ_ELECT_HIGH = warning. Flipped
  `READY_TO_SEED â†’ True` â†’ math gate stayed green â†’ **seeded: RS DB 65â†’66 forms, FA 232â†’240** (SCHEDULE_J
  created; all 20 rules cited). **Deployed export verified HTTP 200** (`lookup/SCHEDULE_J/export/`
  53,036 B; 42 facts/20 rules/25 line_map/5 diagnostics/10 tests/4 sources). Committed tts-tax-app
  canonical `server/specs/schedule_j_spec.json` + **8 FA staged** in
  `flow_assertions_1040_schedule_j_pending.json` (status:active; active 1040 gate stays 249 until the
  assertions build leg).
- **Spec-first probe re-confirmed NO RS Schedule J spec** (SCHEDULE_J / 1040_SCHJ / SCHJ / J / f1040sj
  all 404; RS up, real 404s). Per the MANDATORY Rule Studio rule + Division of Authority: drafted the
  loader for Ken's review â€” did NOT improvise income-averaging compute.
- **Loader `specs/management/commands/load_1040_schedule_j.py`** â€” SCHEDULE_J (42 facts / 20 rules / 25
  lines / 5 diagnostics / 10 scenarios / 23 rule_links) + 8 FA. Pre-seed: guard verified REFUSING (zero
  DB writes; id-length â‰¤20 guards pass). 4 new sources (Sch J form/instr, the Schedule D Tax Worksheet,
  IRC Â§1301 [requires_human_review]); 2 new topics. NO amendment (single new form).
- **LAW VERIFIED 2026-06-21 against the actual 2025 IRS PDFs (pymupdf dumps) â€” NOT memory**
  (tts-tax-app `server/specs/_schedule_j_source_brief.md`, sha256s in Â§1):
  - **23-line chain** (f1040sj): L3=L1âˆ’L2a; L4=tax(L3) current-year; L6=round(L2a/3); L7=max(0,L5+L6);
    L11=L9+L6 & L15=L13+L6 (signed); L8/12/16 = base-year tax on L7/L11/L15 (0 when â‰¤0); L17=4+8+12+16;
    L22=19+20+21; **L23=L18âˆ’L22 â†’ 1040 line 16** (route gate, only when elected). Base years (TY2025) =
    2022/23/24; (TY2026) = 2023/24/25.
  - **Base-year RATE SCHEDULES 2022/23/24** (i1040sj pp.4/8/12, all 4 statuses) + **base-year QDCGT**
    (27-line) + **Schedule D Tax Worksheet** (i1040sd â€” IDENTICAL 47-line structure 2022/23/24/25, only
    3 breakpoint sets differ â†’ ONE year-keyed engine). **KEY override:** base-year tax uses the base-year
    RATE SCHEDULE for the ordinary sub-tax, NEVER the Tax Table. **Stale-cross-ref:** instr cite SDTW
    "34/36"(2022)/"42/44"(2023) but the real worksheets are 44/46 â€” implement 44/46.
- **MATH GATE `check_schedule_j_integrity.py` ALL CHECKS PASS** â€” independent re-type of the 23-line
  chain over re-typed rate schedules (SJ-T1: L4=21,647 / L8=6,617 / L12=7,408 / L16=8,253 / L23=31,982 <
  regular 36,047), the negative/floor (SJ-T2 L12=0) + line-6 round-half-up (SJ-T10) + differing-status
  (SJ-T9); loader rate schedules / preferential breakpoints / SDTW mid threshold cross-checked
  cell-by-cell. Loader & gate share no math.
- **v1 SCOPE (Ken-locked 2026-06-21, AskUserQuestion):** IN â€” the chain + elected farm income incl. net
  capital gain (2b/2c); L4/8/12/16 route rate-schedule/QDCGT/SDTW year-keyed; **build SDTW + base-year
  QDCGT**; base-year amounts DIRECT ENTRY (+ PriorYearReturn pull). RED-defer (each a D_SJ_*):
  prior-Sch-J chaining (D_SJ_CHAIN), zero-or-less Taxable-Income worksheets (D_SJ_NEG_TI warning), Form
  2555/FEI (D_SJ_2555). Plus D_SJ_2A_EXCEED, D_SJ_ELECT_HIGH.
- **WALK ITEMS (requires_human_review, brief Â§10):** **A â€” line-4 capital-gain netting** (does the
  current-year SDTW reduce Sch D figures by 2b/2c when 2b>0? recommend yes-reduce floored at 0 â€”
  LOAD-BEARING, confirm vs Â§1301/Reg 1.1301-1); B â€” line-6 rounding (recommend round-half-up whole
  dollar); C â€” stale SDTW cross-ref (confirm 44/46); D â€” elect-when-higher warning-only.
- **Next (tts-tax-app): the 6 build legs** â€” seed (`ScheduleJ` OneToOne model + migration + RLS +
  serializer/CRUD + `seed_schedule_j` + `f1040sj` manifest; merge the 2022/23/24 base-year schedules
  into the spine `TAX_BRACKETS`) â†’ compute (`compute_schedule_j.py`: the 23-line chain + the year-keyed
  rate-schedule/QDCGT/SDTW engines [reuse the Topic-3 QDCGT engine; NEW year-keyed SDTW] + `route_line_16`
  when elected + RED diagnostics) â†’ render (`f1040sj_2025.py` 2-page map + statement pages for the
  base-year worksheets) â†’ input (new `schedule_j` tab; per-base-year cards) â†’ diagnostics
  (`rules_schedule_j.py` â€” the 5 D_SJ_*) â†’ assertions (merge the 8 FA via `merge_schedule_j_assertions.py`
  + `_run_schj_assertion`; gate 249â†’257). Design precedent: `load_1040_schedule_f.py` / `compute_intdiv.py`.

## 2026-06-21 â€” SCHEDULE_F (1040 farm, cash-method v1) + SCHEDULE_SE farm-optional amendment â€” SEEDED + EXPORTED âœ…
- **Ken APPROVED the review walk in-session ("Approve & seed")** + chose Schedule J = **fast-follow**
  (its own form unit). Flipped `READY_TO_SEED â†’ True` â†’ math gate stayed green â†’ **seeded: RS DB
  64â†’65 forms, FA 224â†’232** (SCHEDULE_F created; SCHEDULE_SE amended; both forms all-rules-cited).
  **Deployed exports verified HTTP 200** (`lookup/SCHEDULE_F/export/` 49,790 B; `SCHEDULE_SE` 33,791 B
  re-exported); committed tts-tax-app canonical `server/specs/schedule_f_spec.json` + re-committed
  `schedule_se_spec.json` + **8 FA staged** in `flow_assertions_1040_schedule_f_pending.json`
  (status:active; active 1040 gate stays 241 until the assertions build leg).
- **SEED GOTCHA:** `FormDiagnostic.diagnostic_id` is **varchar(20)** â€” `D_SE_FARMOPT_INELIGIBLE` (23)
  raised `DataError` (atomic rollback, zero partial writes). Renamed â†’ `D_SE_FARMOPT_INELIG` (19) +
  **hardened the math gate** with rule_id/diagnostic_id/line_number â‰¤20 guards (caught pre-seed next time).
- **Authoring details (below) unchanged.** AUTHORED + MATH-GATED:
- **Spec-first probe re-confirmed NO RS Schedule F spec** (SCHEDULE_F / 1040_SCHF / F / SCHF all 404;
  RS up, real 404s). Per the MANDATORY Rule Studio rule + Division of Authority: drafted the loader
  for Ken's review â€” did NOT improvise farm-tax compute.
- **NEW loader `specs/management/commands/load_1040_schedule_f.py`** â€” creates **SCHEDULE_F** (31 facts /
  11 rules / 71 lines / 8 diagnostics / 10 scenarios / 14 rule_links) and **AMENDS SCHEDULE_SE** additively
  (10 facts / 2 rules / 7 lines / 3 diagnostics / 4 scenarios / 3 rule_links â€” the Part II FARM OPTIONAL
  METHOD + line-1a/1b computed-feeder re-point + narrowed R-SE-OPTIONAL/D_SE_003) + **8 flow assertions
  FA-1040-SCHF-01..08**. `READY_TO_SEED = False` â€” **guard verified REFUSING (zero DB writes; "(all
  populated)")**. 6 new sources (Sch F form/instr, Pub 225 [requires_human_review], IRC Â§77 / Â§451(e)(f) /
  Â§1402(a)(1)); 2 new topics. RS DB still 64 forms (nothing seeded).
- **LAW VERIFIED 2026-06-21 against the actual 2025 IRS PDFs (pymupdf dumps) â€” NOT memory**
  (tts-tax-app `server/specs/_schedule_f_source_brief.md`):
  - **Line 9 gross income = 1c + 2 + 3b + 4b + 5a + 5c + 6b + 6d + 7 + 8** (verbatim right-column list;
    includes BOTH 5a [CCC elected] and 5c [forfeiture taxable], NOT 5b). L1c = 1a âˆ’ 1b. L33 = sum(10..32f).
    **L34 = L9 âˆ’ L33 â†’ Schedule 1 line 6 (sum farms) + Schedule SE line 1a (per proprietor); CRP â†’ SE 1b.**
    Sch F has NO home-office line. L14 depreciation â† 4562; farm net â†’ 8995 QBI.
  - **Schedule SE Part II farm optional method (2025, off the face):** eligible iff gross farm income â‰¤
    **$10,860** OR net farm profit < **$7,840**; line 14 max = **$7,240**; line 15 = min(â…” Ã— gross farm
    income, $7,240) â†’ line 4b. SSA-indexed (NOT in RP 2025-32); **2026 UNPUBLISHED â†’ fires RED
    (D_SE_FARMOPT_2026) + standing re-pin** (the Tax-Table-interim precedent).
- **MATH GATE `check_schedule_f_integrity.py` ALL CHECKS PASS** â€” independent re-type of the line
  1c/9/33/34 chain (incl. 5a-in-9 / 6a-not-in-9 membership + multi-farm aggregation) + the farm-optional
  â…”/cap/eligibility/2026-RED; loader & gate share no math; loader constants cross-checked cell-by-cell.
- **v1 SCOPE (Ken-locked):** cash method; per-farm (multi-Schedule-F); farm optional SE IN. **RED-defer
  (no silent gap, each a D_SF_*/D_SE_*):** accrual Part III; CCC Â§77 / crop-insurance Â§451(f) / weather
  Â§451(e) ELECTIONS (capture the $, flag the election); passive loss (line E No â†’ Form 8582); at-risk
  (36b â†’ Form 6198); Â§461(l). Nonfarm optional / church / clergy SE stay RED (D_SE_003 narrowed).
- **WALK ITEMS (requires_human_review):** A) 2026 farm-optional constants unpublished â†’ 2025 supported,
  2026 RED + re-pin; B) Schedule J bundle-vs-fast-follow; C) Pub 225 narrative definitions / Â§77 Â§451
  RED-defer treatment; D) QBI farm-reduction allocation when a proprietor has both a Sch C and a Sch F.
- **Next (tts-tax-app): the 6 build legs** â€” seed (new per-farm ScheduleF FK model + migration + RLS +
  serializer/CRUD + seed command + manifest; flip Sch 1 L6 + Sch SE L1a computed; extend
  `compute_schedule_se_lines` for Part II farm optional) â†’ compute (`compute_schedule_f.py`: line
  1c/9/33/34 + cross-form routing addends + RED diagnostics; QBI â†’ 8995; depreciation 4562 flow_to) â†’
  render (un-stub `f1040sf_2025.py` field map â€” 89 PDF fields; cash-method Parts I/II + line 34; skip
  page 2) â†’ input (un-stub the `schedule_f` React tab; per-farm card UI) â†’ diagnostics (`rules_schedule_f.py`)
  â†’ assertions (merge the 8 FA via `merge_schedule_f_assertions.py` + `_run_schf_assertion`; gate 241â†’249).
  Then **Schedule J** as the fast-follow (its own RS spec). Design precedent: `load_1040_schedule_c.py`.

## 2026-06-21 â€” SCHEDULE_K1 (recipient K-1 router, effort #5) + SCHEDULE_E page-2 amendment â€” SEEDED + EXPORTED âœ…
- **Ken approved the review walk in-session ("Approve & seed as authored").** The RECIPIENT-side K-1
  full router (TaxWise/Lacerte model): a 1040 partner (1065 K-1) / S-corp shareholder (1120-S K-1) /
  estate-trust beneficiary (1041 K-1) routing EVERY box to its destination. NEW form **SCHEDULE_K1**
  (31 facts / 11 rules / 21 lines / 10 diagnostics / 12 scenarios / 18 links) + **SCHEDULE_E AMENDED**
  additively with page 2 (Parts II-V lines 27-43; +3 rules R-SCHE-P2-*; +2 diags D_SCHE_REMIC/4835) +
  7 flow assertions FA-1040-K1-01..07. `check_schedule_k1_integrity.py` **ALL CHECKS PASS** (independent
  re-type of the page-2 aggregation + cross-form routing; loader & gate share no math). Guard verified
  REFUSING before the flip (zero DB writes). **RS DB 63â†’64 forms, FA 217â†’224.** All rules cited. 6 new
  sources (i1065sk1 / i1120ssk / i1041sk1 / Â§199A / Â§1402 / Â§702-1366-652 conduit), the 3 K-1 instruction
  sources `requires_human_review=True`.
- **LAW VERIFIED 2026-06-21 against the actual 2025 IRS PDFs (pymupdf dumps) + the K-1 instruction
  booklets â€” NOT memory** (tts-tax-app `server/specs/_schedule_k1_source_brief.md`):
  - **âš  CORRECTION to the brainstorm design spec:** the summary that flows to Schedule 1 line 5 is
    Schedule E **line 41** ("Combine lines 26, 32, 37, 39, and 40"), NOT line 40 (= Form 4835 farm
    rental) â€” the brainstorm recalled it wrong. Encoded line 41 = 26+32+37+39+40 â†’ Sch 1 L5.
  - Part II (1065/1120-S) line 28 cols (g) passive loss / (h) passive income / (i) nonpassive loss /
    (j) Â§179 / (k) nonpassive income â†’ 30/31/32. Part III (1041) line 33 cols (c)/(d)/(e)/(f) â†’ 35/36/37.
  - **Â§199A codes:** 1065 box **20Z**, 1120-S box **17V**, 1041 box **14I** â€” all "Section 199A
    information" â†’ Form 8995 (QBI line 2; REIT/PTP line 6). **SE:** 1065 box **14 code A** â†’ Schedule SE;
    "S corporation income isn't subject to self-employment tax" (no S-corp/1041 SE).
- **v1 scope (Ken Decisions 1-6, 2026-06-21):** full router; sources 1065+1120-S+1041; **passive losses
  RED-deferred** (route passive income + all nonpassive; passive loss â†’ RED "limit via 8582 manually");
  Â§199A â†’ 8995 IN; partnership SE â†’ Sch SE IN. RED-defer (no silent gap, each a D_K1_*): passive loss,
  Â§1231â†’4797, 28%/Â§1250â†’SDTW, AMTâ†’6251, basis/at-risk (warning), other income, foreign/K-3, PTP (warning),
  REMIC, Form 4835.
- **Deployed exports verified HTTP 200** (`lookup/SCHEDULE_K1/export/` 59,809 B; `SCHEDULE_E` 29,748 B â€”
  re-exported since amended); committed to tts-tax-app as canonical `server/specs/schedule_k1_spec.json` +
  re-committed `schedule_e_spec.json` + 7 FA staged in `flow_assertions_1040_schedule_k1_pending.json`
  (status:active; active 1040 gate 234 unchanged until the assertions build leg). Source brief
  `server/specs/_schedule_k1_source_brief.md`.
- **WALK ITEMS (requires_human_review, Ken's recommendation accepted):** (1) severity split â€” passive
  loss=error, basis/at-risk=warning; (2) 1041 boxes 6/7/8 default to material-participation (preparer
  toggles per-K-1); (3) Â§199A split into two facts (QBI line 2 + REIT/PTP line 6); (4) PTP loss = warning
  (per-PTP netting bounded out of v1).
- **Next (tts-tax-app): the 6 build legs** â€” seed (new per-entity K-1 recipient model + migration + RLS +
  serializer/CRUD + seed command + manifest) â†’ compute (`compute_schedule_e_p2.py`/extend: K-1 aggregation
  + line-41 summary + cross-form routing addends + RED diagnostics) â†’ render (extend `f1040se_2025.py`
  Parts II/III/V) â†’ input (un-stub `schedule_e_p2`; per-entity K-1 UI) â†’ diagnostics (`rules_schedule_e_p2.py`)
  â†’ assertions (merge 7 FA + `_run_k1_assertion`; **REPOINT FA-1040-SCHE-01 line 26 â†’ line 41**). Design
  doc tts-tax-app `docs/superpowers/specs/2026-06-21-effort5-schedule-e-p2-k1-router-design.md`.

## 2026-06-20 â€” Form W-2G (certain gambling winnings Â§61, effort #4) spec leg â€” SEEDED + EXPORTED âœ…
- **Ken approved the review walk in-session ("Approve & seed as recommended").** Flipped
  `READY_TO_SEED â†’ True` â†’ `check_w2g_integrity.py` **ALL CHECKS PASS** â†’ **seeded FORM_W2G** (7 facts /
  2 rules / 6 lines / 2 diagnostics / 5 scenarios / 5 cited links + 5 flow assertions; 4 authority
  sources: IRC Â§61, IRC Â§165(d), Instr. W-2G & 5754 box layout, 2025 i1040 Sch 1 L8b + 1040 L25c).
  **RS DB â†’63 forms, FA â†’217.** All rules cited. Mirrors the 1099-G vertical (same input-document
  shape, simpler: no repayment netting, no Â§1341).
- **Deployed export verified HTTP 200** (`lookup/FORM_W2G/export/`, 12,733 bytes); committed to
  tts-tax-app as canonical `server/specs/w2g_spec.json` + 5 FA staged in
  `flow_assertions_1040_w2g_pending.json` (active 1040 gate unchanged until the Part-B assertions leg).
- **Scope (Ken):** (1) pull W-2G into effort #4 WITH compute (a FormW2G doc sub-model â†’ Sch 1 L8b +
  1040 L25c). (2/recommended, confirm at walk) line 8b = Î£ box1 + a return-level `other_gambling_winnings`
  (non-W-2G winnings) so 8b is the TOTAL (it backs the Sch A Â§165(d) loss cap).
- **KEY ROUTING (verified vs IRS, not memory):** box 1 winnings â†’ **Sch 1 line 8b** ("Gambling"); box 4
  federal withholding â†’ **1040 line 25c** ("Other forms") â€” **NOT 25b** (W-2G is not a 1099). Line 25c is
  a **roster** shared with Form 8959 (additional-Medicare withholding), so the tts-tax-app compute must
  ADD W-2G box 4 to 25c, not clobber the 8959 write (FA-1040-W2G-05 guards this). No render face (input
  document, like 1099-G / W-2). No year-keyed constants (Â§61 identical 2025/2026).
- **WALK ITEMS (requires_human_review):** confirm the exact 2025/2026 i1040 wording + line numbers (8b,
  25c); confirm the W-2G box numbering vs the target-year revision (box 1/4/15 stable across recent revs).
- **Next:** Ken review walk â†’ flip READY_TO_SEED â†’ seed (RS DB +1 form, FA +5) â†’ verify deployed export â†’
  commit canonical `server/specs/w2g_spec.json` + stage assertions in `flow_assertions_1040_w2g_pending.json`
  â†’ then tts-tax-app build legs (model 0096+ â†’ serializer/CRUD â†’ compute â†’ diagnostics â†’ input/Misc Income
  page â†’ assertions). Spec/design doc: tts-tax-app `docs/superpowers/specs/2026-06-20-effort4-retirement-misc-reorg-design.md`.

## 2026-06-16 â€” MINISTER (Minister/Clergy Housing Allowance & SE Tax Â§107/Â§1402, W-2 Unit 4) spec leg â€” SEEDED + EXPORTED âœ…
- **Ken approved the review walk in-session ("Looks good. Continue")** â€” a worksheet-style spec (NOT a
  single IRS form; reconstructed from Pub 517) for the church-employed (common-law-employee) minister's
  DUAL STATUS: income-tax EMPLOYEE (W-2) but SELF-EMPLOYED for SE tax. INCOME TAX (Â§107): housing/rental
  allowance excluded up to the **least of (designated / used / FRV+utilities)**; the EXCESS â†’ **Form 1040
  line 1h** ("Excess allowance"). SE TAX (Â§1402(a)(8)): the FULL housing allowance + parsonage FRV go BACK
  into the SE base â€” **Schedule SE line 2 = wages + housing allowance + parsonage FRV âˆ’ unreimbursed
  ministerial expenses** (full; no Deason for SE); the EXISTING Topic-8 SE engine applies Ã— 0.9235 + the
  SS cap + Â½-SE â†’ Sch 1 L15 + SE â†’ Sch 2 L4. **Form 4361** approved â†’ Schedule SE line 2 = 0.
- LAW VERIFIED 2026-06-16 vs IRS Pub 517 (2025) + IRC Â§107 + Â§1402(a)(8)/(c)(4)/(e) (live WebFetch):
  the Â§107 least-of-three; the Â§1402(a)(8) housing-in-SE inclusion ("doesn't apply for SE tax purposes",
  Pastor Leslie Adams example $39k+$12k=$51k SE); excess â†’ 1040 1h; W-2 minister wages â†’ Schedule SE
  line 2 (no Schedule C, no FICA); Form 4361 omits ministerial earnings. Â½-SE-tax (Sch 1 L15) normal.
- **KEN'S 3 SCOPE DECISIONS (2026-06-16 AskUserQuestion):** (1) v1 = "W-2 minister core" (RED-defer
  Schedule-C ministerial side income, Â§265/Deason allocation, retired-minister housing, 4361
  adjudication); (2) clergy inputs ON `W2Income` + a person-level `clergy_4361_exempt` Taxpayer fact;
  (3) include one preparer-entered unreimbursed-ministerial-expenses input (full, for SE).
- `load_1040_minister.py` + `check_minister_integrity.py` **ALL CHECKS PASS** (independent re-type of
  the Â§107 least-of-three + the Â§1402(a)(8) SE base + the Form 4361 zeroing + all 6 scenarios + the 6
  diagnostic conditions + negative-floor/below-FRV edges; loader & gate share no math). Guard verified
  REFUSING before the flip.
- Flipped READY_TO_SEED â†’ seeded: **MINISTER** (10 facts / 4 rules / 11 lines / 6 diagnostics / 6
  scenarios / 7 links) + 6 flow assertions. **RS DB 61â†’62 forms, FA 206â†’212.** All rules cited. 4
  sources (Pub 517 / Â§107 / Â§1402 / Form 4361), all `requires_human_review=True`.
- **WALK ITEMS (requires_human_review):** (a) the worksheet line LABELS are reconstructed from the Pub
  517 narrative + examples (PDF worksheet tables don't render in HTML) â€” the COMPUTATION is math-gated;
  (b) the SE housing component uses the full DESIGNATED allowance (line 2), confirmed vs Â§1402(a)(8) +
  the Pastor Adams example; (c) reasonable-comp Â§107 limit NOT modeled (D_MIN_REASONABLE info); (d)
  Form 4361 preparer-asserted, not adjudicated.
- Deployed export verified HTTP 200 (`lookup/MINISTER/export/`, 24,185 bytes; 10/4/11/6/6/4); committed
  to tts-tax-app as canonical `server/specs/minister_spec.json` + 6 FA staged in
  `flow_assertions_1040_minister_pending.json` (active 1040 gate stays 223). Source brief
  `server/specs/_minister_source_brief.md`.
- Next (tts-tax-app): the 6 build legs â€” seed (clergy fields on W2Income + `clergy_4361_exempt` Taxpayer
  fact + migration) â†’ compute (`compute_minister.py` â†’ 1040 line 1h + a clergy Schedule SE row at line 2
  feeding the existing SE engine) â†’ render (Pub 517 worksheet statement, the SM-statement precedent) â†’
  input (clergy fields on the W2Screen FieldGrid) â†’ diagnostics (`rules_minister.py`, 6) â†’ assertions
  (merge the 6 FA + `_run_minister_assertion`) â†’ tag `1040-minister-complete`.

## 2026-06-15 â€” Form 7206 (Self-Employed Health Insurance Deduction Â§162(l), W-2 Unit 3) spec leg â€” SEEDED + EXPORTED âœ…
- **Ken approved the review walk in-session ("Approved â€” seed it")** â€” the Â§162(l) SEHI deduction
  â†’ Schedule 1 line 17, computed on **Form 7206** (the form that replaced the old SEHI worksheet
  since TY2023). TWO earned-income limit paths on one form: the **Sch C/SE path** (line 10 = net
  profit âˆ’ apportioned Â½-SE-tax line 7 âˆ’ SEP/SIMPLE line 9) and the **S-corporation 2% shareholder
  path** (line 4 "skip to line 11"; line 11 = **Box 5 Medicare wages**). Line 14 = min(line 3
  premiums, line 13 limit); the return total = Î£ each form's line 14. **One Form 7206 per business.**
- LAW VERIFIED 2026-06-15 cell-by-cell from the 2025 Form 7206 PDF (pulled via pymupdf) + i7206 +
  Â§162(l)(2)(A): the 2% shareholder limit is the **W-2 Box 5** Medicare wages (form line 11 verbatim);
  no Â½-SE-tax reduction on the S-corp path (no SE tax). Form 2555 line 12 RED-deferred (v1 = 0); LTC
  line 2 folded into the premium input (preparer age-capped) â€” no auto-cap, no new model field.
- `load_1040_form_7206.py` + `check_form_7206_integrity.py` **ALL CHECKS PASS** (independent re-type
  of both limit paths + the smaller-of + all 8 scenarios + the 3 limit diagnostics; loader & gate
  share no math). Guard verified REFUSING before the flip.
- **Ken's 2 decisions (AskUserQuestion):** (1) author a Form 7206 RS spec (not a bare engine
  extension); (2) **fix the existing Schedule C SEHI limit** â€” the old R-SC-SEHI capped only at net
  profit, NOT subtracting the Â½-SE-tax / SE-retirement. Scenario **SC-T6** pins the fix (net 5,000 /
  Â½-SE 700 / premium 6,000 â†’ deduction **4,300**, was 5,000).
- Flipped READY_TO_SEED â†’ seeded: **FORM_7206** (12 facts / 4 rules / 15 lines / 6 diagnostics / 8
  scenarios / 7 links) + 6 flow assertions. **RS DB 60â†’61 forms, FA 200â†’206.** All rules cited. 3
  sources (Form 7206 / i7206 / IRC Â§162(l)).
- **R-SC-SEHI updated in lock-step (Ken's call):** `load_1040_schedule_c.py` R-SC-SEHI formula +
  description repointed to FORM_7206 (text-only, no count change); Schedule C re-seeded (TaxForms 61,
  FA 206 unchanged).
- Deployed export verified HTTP 200 (`lookup/FORM_7206/export/`, 20,856 bytes; 12/4/15/6/8/3);
  committed to tts-tax-app as canonical `server/specs/7206_spec.json` + 6 FA staged in
  `flow_assertions_1040_7206_pending.json` (active 1040 gate stays 217).
- Next (tts-tax-app): build legs â€” compute (`compute_7206` replacing `sehi_deduction_for_proprietor`:
  Sch C limit fix + the S-corp Box-5 path; new engage so a no-Schedule-C 2%-shareholder return writes
  Sch 1 L17; the existing 8962 SEHIâ†”PTC iterative reads line 17 source-agnostically) â†’ diagnostics â†’
  assertions â†’ tag.

## 2026-06-15 â€” Form 2210 (underpayment of estimated tax Â§6654, Phase 2 sixth common form) spec leg â€” SEEDED + EXPORTED âœ…
- **Ken approved the review walk in-session ("Approved â€” seed it, include render")** â€” the FULL build:
  Part I safe harbors ($1,000 de-minimis / 90% / 100% / 110% over $150k AGI), the Regular Method
  penalty (Â§6621 7% through 3/31/2026, 6% for 4/1-4/15/2026 â€” verified web vs the 2025 Rev. Ruls.),
  and Schedule AI (factors 4/2.4/1.5/1, applicable % 22.5/45/67.5/90, smaller-of). Ken's 2 scope
  decisions: FULL (regular + annualized); prior-year inputs as preparer facts.
- `load_1040_2210.py` + `check_2210_integrity.py` ALL CHECKS PASS (independent re-type of the Â§6654
  safe harbors + the Â§6621 penalty day-factors + Schedule AI + all 6 numeric scenarios, AND cross-
  checks the loader's compute_2210; loader & gate share no math). Guard verified REFUSING.
- Flipped READY_TO_SEED â†’ seeded: **FORM_2210** (10 facts / 3 rules / 11 lines / 5 diagnostics / 7
  scenarios / 5 cited links) + 6 flow assertions. **RS DB â†’60 forms, FA â†’200.** All rules cited. 2
  sources (i2210 / IRC Â§6654).
- **KEY:** penalty â†’ 1040 line 38 (already the manual NIIT... no, the est-tax-penalty slot, direct-
  entry â†’ now computed). Â§6621 penalty day-factors [0.069589, 0.057890, 0.040247, 0.016849] for the 4
  periods (due 4/15, 6/15, 9/15/2025, 1/15/2026). **WALK ITEMS (requires_human_review):** Schedule AI
  takes the per-period annualized TAX as a preparer input (t2210_ai_tax_q*; the full per-period
  bracket/QDCGT/AMT computation deferred); withholding spread evenly (no actual-date election); Part
  II waiver + farmers/fishermen out of v1. TY2026 â†’ re-pin the Â§6621 rates.
- Deployed export verified HTTP 200 (`lookup/FORM_2210/export/`); committed to tts-tax-app as canonical
  `server/specs/2210_spec.json` + 6 FA staged in `flow_assertions_1040_2210_pending.json` (active 1040
  gate stays 189).
- Next (tts-tax-app): the 6 build legs â€” seed (~10 t2210_* Taxpayer facts + a FORM_2210 FormDef) â†’
  compute (`compute_2210.py` â†’ 1040 line 38; reads current tax/withholding/est payments, runs near the
  end of the 1040 pass) â†’ render (f2210.pdf incl. Schedule AI) â†’ input â†’ diagnostics â†’ assertions â†’
  tag `1040-form-2210-complete`.

## 2026-06-15 â€” Form 8960 (net investment income tax Â§1411, Phase 2 fifth common form) spec leg â€” SEEDED + EXPORTED âœ…
- **Ken approved the review walk in-session ("Approved â€” seed it, include render")** â€” the 3.8% NIIT
  on min(net investment income, MAGI âˆ’ threshold); the auto-feed (interest 1040 2b / dividends 3b /
  net gain line 7) + the Â§1411 adjustments on 4b/5b/6/7; the MAGI = AGI + Â§911 base; the statutory
  thresholds. Ken's 2 scope decisions: auto-aggregate clean feeders + overrides; Â§1411 nuances are
  preparer adjustments via 4b/6/7.
- `load_1040_8960.py` + `check_8960_integrity.py` ALL CHECKS PASS (independent re-type of the Â§1411
  chain + the thresholds + all 7 numeric scenarios; loader & gate share no math). Guard verified REFUSING.
- Flipped READY_TO_SEED â†’ seeded: **FORM_8960** (17 facts / 3 rules / 15 lines / 5 diagnostics / 8
  scenarios / 5 cited links) + 6 flow assertions. **RS DB â†’59 forms, FA â†’194.** All rules cited. 2
  sources (i8960 / IRC Â§1411).
- **KEY:** NIIT = 3.8% Ã— min(max(0, line 12 NII), MAGI âˆ’ threshold) â†’ Schedule 2 line 12 (already the
  NIIT slot, direct-entry â†’ now computed). Thresholds STATUTORY/non-indexed (MFJ/QSS $250k, MFS $125k,
  single/HoH $200k) â€” same 2025/2026. MAGI = AGI + Â§911 (the 8962 base). Return-level facts (no
  sub-model â€” per-return tax). RED-deferred: estates/trusts, the disposition-of-active-interest
  worksheet, the precise state-tax allocation ratio.
- Deployed export verified HTTP 200 (`lookup/FORM_8960/export/`); committed to tts-tax-app as canonical
  `server/specs/8960_spec.json` + 6 FA staged in `flow_assertions_1040_8960_pending.json` (active 1040
  gate stays 183).
- Next (tts-tax-app): the 6 build legs â€” seed (~12 e8960_* Taxpayer facts + a FORM_8960 FormDef) â†’
  compute (`compute_8960.py` â†’ Schedule 2 line 12; auto-feeds interest 2b / dividends 3b / gain line 7;
  MAGI from AGI; runs after AGI final) â†’ render (f8960.pdf) â†’ input â†’ diagnostics â†’ assertions â†’ tag
  `1040-form-8960-complete`.

## 2026-06-15 â€” Form 8606 (nondeductible IRAs Â§408(d)+Â§408A, Phase 2 fourth common form) spec leg â€” SEEDED + EXPORTED âœ…
- **Ken approved the review walk in-session ("Approved â€” seed it, include render")** â€” the Â§408(d)
  pro-rata (nontaxable% = basis / (year-end + distributions + conversions), capped 1.0), the Part II
  conversion taxable (line 18 = line 16 âˆ’ the line-11 pro-rata basis), the Â§408A(d)(4) Roth ordering
  (contributionsâ†’conversionsâ†’earnings), and the 1099-R box-2a SUPERSESSION on line 4b. Ken's 3 scope
  decisions: ALL THREE PARTS; a per-owner Form8606 sub-model; the 8606 supersedes the 1099-R box-2a.
- `load_1040_8606.py` + `check_8606_integrity.py` ALL CHECKS PASS (independent re-type of part_i/
  part_ii/part_iii + all 7 numeric scenarios incl. basis conservation; loader & gate share no math).
  Guard verified REFUSING.
- Flipped READY_TO_SEED â†’ seeded: **FORM_8606** (16 facts / 4 rules / 22 lines / 6 diagnostics / 8
  scenarios / 6 cited links) + 6 flow assertions. **RS DB â†’58 forms, FA â†’188.** All rules cited. 3
  sources (i8606 / IRC Â§408(d) / IRC Â§408A).
- **KEY:** the 8606 owner-with-basis taxable amount (line 15c + 18 + 25c) drives 1040 line 4b,
  SUPERSEDING the 1099-R box-2a (the Simplified Method precedent â€” the gross 4a still sums). **WALK
  ITEM:** line 17 = line 11 (the pro-rata; the IRS "line 2 + pre-conversion line 1" plain-language form
  equals line 11 in the no-other-IRA backdoor case â€” i8606 requires_human_review). RED-deferred:
  disaster distributions, outstanding rollovers, recharacterizations, inherited-IRA basis.
- Deployed export verified HTTP 200 (`lookup/FORM_8606/export/`); committed to tts-tax-app as canonical
  `server/specs/8606_spec.json` + 6 FA staged in `flow_assertions_1040_8606_pending.json` (active 1040
  gate stays 177).
- Next (tts-tax-app): the 6 build legs â€” seed (a per-owner Form8606 sub-model + mig + RLS + FORM_8606
  FormDef + CRUD) â†’ compute (`compute_8606.py` â†’ 1040 line 4b, superseding the 1099-R IRA box-2a; runs
  in/after compute_retirement_aggregation, re-deriving 4b) â†’ render (f8606.pdf, one copy per owner) â†’
  input â†’ diagnostics â†’ assertions â†’ tag `1040-form-8606-complete`.

## 2026-06-15 â€” Form 5695 (residential energy credits Â§25D+Â§25C, Phase 2 third common form) spec leg â€” SEEDED + EXPORTED âœ…
- **Ken approved the review walk in-session ("Approved â€” seed it, include render")** â€” the Â§25D 30% +
  fuel-cell $500/Â½kW cap + carryforward + tax limit; the Â§25C caps ($1,200 aggregate + $250/$500 doors
  / $600 windows / $600-per-item / $150 audit + the separate $2,000 heat-pump group, max $3,200); the
  OBBBA termination after 2025. Ken's 2 scope decisions: both parts with caps modeled; model the
  tax-liability limit + the Â§25D carryforward. Render INCLUDED (full 6-leg build).
- `load_1040_5695.py` + `check_5695_integrity.py` ALL CHECKS PASS (independent re-type of credit_25d/
  credit_25c + all 8 numeric scenarios; loader & gate share no math). Guard verified REFUSING. Fix:
  the loader was missing the FormRule import (NameError on first seed) â†’ added.
- Flipped READY_TO_SEED â†’ seeded: **FORM_5695** (21 facts / 4 rules / 15 lines / 6 diagnostics / 9
  scenarios / 7 cited links) + 6 flow assertions. **RS DB â†’57 forms, FA â†’182.** All rules cited. 3
  sources (i5695 / IRC Â§25D / IRC Â§25C).
- **KEY:** TY2025-only â€” OBBBA terminates BOTH credits after 12/31/2025 (D_5695_2026 RED for 2026+).
  Â§25D â†’ Sch 3 5a (carries forward); Â§25C â†’ Sch 3 5b (no carryforward, excess lost). The Credit Limit
  Worksheet ordering is simplified in v1 (i5695 requires_human_review). Deferred: joint occupancy,
  QM-PIN/CEE-tier qualification, per-door/window itemization.
- Deployed export verified HTTP 200 (`lookup/FORM_5695/export/`); committed to tts-tax-app as canonical
  `server/specs/5695_spec.json` + 6 FA staged in `flow_assertions_1040_5695_pending.json` (active 1040
  gate stays 171).
- Next (tts-tax-app): the 6 build legs â€” seed (FORM_5695 FormDef + ~21 e5695_* Taxpayer facts, the
  Sch-A/8889 return-level precedent) â†’ compute (`compute_5695.py` â†’ Sch 3 5a/5b; in the Sch-3 credit
  block, needs tax liability for the Credit Limit Worksheet) â†’ render (download f5695.pdf) â†’ input â†’
  diagnostics â†’ assertions â†’ tag `1040-form-5695-complete`.

## 2026-06-14 â€” Form 1099-G (unemployment, Phase 2 second common form) spec leg â€” SEEDED + EXPORTED âœ…
- **Ken approved the review walk in-session ("Approved â€” seed it; no render form")** â€” Â§85
  full inclusion (NO exclusion for 2025/2026; the 2020 ARPA $10,200 was COVID-only), the
  same-year-repayment netting on Sch 1 line 7 (the "Repaid" literal), box 4 â†’ 1040 line 25b,
  the Â§1341 prior-year-repayment RED, the box-5/6/7/9 RED, box 2 stays in STATE_REFUND.
- `load_1040_1099g.py` + `check_1099g_integrity.py` ALL CHECKS PASS (independent re-type of
  max(0, box1âˆ’repaid) summed + the box-4 aggregation + a "no exclusion ever applied" invariant
  + the 7 scenarios; loader & gate share no math). Guard verified REFUSING before the flip.
- Flipped READY_TO_SEED â†’ seeded: **FORM_1099G** (10 facts / 4 rules / 7 lines / 5 diagnostics
  / 7 scenarios / 5 cited links) + 6 flow assertions. **RS DB â†’56 forms, FA â†’176.** All rules
  cited. 3 sources (IRC Â§85 / 2025 i1040 Sch 1 Line 7 / Pub 525).
- **KEY:** NO year-keyed constants â€” Â§85 full inclusion is identical for 2025/2026; the only
  year-sensitivity is the form line numbers (2025 i1040 Sch 1 Line 7 source = requires_human_review,
  re-verify the 2026 1099-G box layout + line 7 number ~Dec 2026). Ken's scope decisions:
  Form1099G doc model; same-year netting computed + Â§1341 RED; v1 box 1+4 only + other-boxes RED.
- Deployed export verified HTTP 200 (`lookup/FORM_1099G/export/`); committed to tts-tax-app as
  canonical `server/specs/1099g_spec.json` + 6 FA staged in `flow_assertions_1040_1099g_pending.json`
  (active 1040 gate stays 165).
- **NO RENDER LEG** (Ken's call) â€” 1099-G is an input document (like W-2), not filed with the
  return; the value renders on Schedule 1 (already built). Build legs (tts-tax-app): seed (a
  Form1099G doc model + mig + RLS + FORM_1099G FormDef + CRUD) â†’ compute (`compute_1099g.py` â†’
  Sch 1 L7 + the 7_repaid literal + 1040 L25b; runs in the pre-formula-pass income feeder block â€”
  line 7 is INCOME, the compute_state_refund_db precedent) â†’ input â†’ diagnostics â†’ assertions â†’
  tag `1040-form-1099g-complete`. RED-deferred: Â§1341 prior-year repayment, boxes 5/6/7/9.

## 2026-06-14 â€” Form 8889 (HSA, Phase 2 first common form) spec leg â€” SEEDED + EXPORTED âœ…
- **Ken approved the review walk in-session ("Looks right.")** â€” the Â§223 limits +
  the catch-up + the deduction (min(own, limitâˆ’employer)) + the proration + the
  last-month rule + the married family split + the distribution/20% (with the
  exception) + Part III/10% + the Sch-2-17c/17d flow correction.
- `load_1040_form_8889.py` + `check_8889_integrity.py` ALL CHECKS PASS (independent
  re-type of the Â§223 limits + the proration + the deduction/distribution/Part-III
  math + the 11 scenarios; loader & gate share no math). Guard verified REFUSING.
- Flipped READY_TO_SEED â†’ seeded: **FORM_8889** (18 facts / 6 rules / 24 lines /
  6 diagnostics / 11 scenarios / 11 cited links) + 6 flow assertions. **RS DB â†’55
  forms, FA â†’170.** All rules cited. 3 sources (i8889 / IRC Â§223 / Pub 969).
- CONSTANTS verified vs Rev. Proc. 2024-25 Â§2.01 (2025) + 2025-19 Â§2.01 (2026):
  self-only/family 2025 $4,300/$8,550, 2026 $4,400/$8,750; $1,000 catch-up (55+,
  statutory, both). FLOW: line 13 â†’ Sch 1 L13; line 16 + line 20 â†’ Sch 1 L8f; line
  17b (20%) â†’ **Sch 2 L17c**; line 21 (10%) â†’ **Sch 2 L17d** (corrected from the
  13c premise â€” both HSA additional taxes live under Sch 2 line 17 "Other").
- Deployed export verified HTTP 200 (`lookup/FORM_8889/export/`); committed to
  tts-tax-app as canonical `server/specs/form_8889_spec.json` + 6 FA staged in
  `flow_assertions_1040_8889_pending.json` (active 1040 gate stays 159).
- Next (tts-tax-app): the 6 build legs â€” seed (a per-owner **HSA** sub-model + RLS,
  the FORM_8889 FormDef + facts) â†’ compute (`compute_8889.py` â†’ Sch 1 L13/L8f + Sch
  2 L17c/L17d; **runs BEFORE compute_sch123** â€” L13 is an above-the-line ADJUSTMENT,
  the compute_state_refund_db precedent) â†’ render (f8889.pdf, per-owner copies) â†’
  input â†’ diagnostics â†’ assertions â†’ tag `1040-form-8889-complete`. RED-deferred:
  the 6% excess excise (5329 Part VII), the IRAâ†’HSA funding distribution, non-spouse
  death. WALK ITEM: re-verify the 2026 Form 8889 line numbers when posted.

## 2026-06-14 â€” State refund worksheet (NEXT-UP #9, the LAST item) spec leg â€” SEEDED + EXPORTED âœ…
- **Ken approved the review walk in-session ("No changes. Continue")** â€” the Â§111
  tax-benefit computation (Pub 525 Worksheet 2 + 2a): the SALT-cap recapture (the
  prior-year Sch A 5d/5e), the itemized-vs-standard difference limit, the negative-
  prior-year-TI reduction, the line-1/line-8z allocation, the Â§111 gates, the
  prior-year std-ded constants (2024 verified / 2025 interim), and the RED-deferred
  AMT/credit/multi-year exceptions.
- `load_1040_state_refund.py` + `check_state_refund_integrity.py` ALL CHECKS PASS
  (independent re-type of Worksheet 2/2a + the 2024/2025 std-ded + the 9 scenarios;
  loader & gate share no math). Guard verified REFUSING before the flip.
- Flipped READY_TO_SEED â†’ seeded: **STATE_REFUND** (19 facts / 5 rules / 17 lines /
  7 diagnostics / 9 scenarios / 8 cited links) + 6 flow assertions. **RS DB â†’54
  forms, FA â†’164.** All rules cited. 3 sources (i1040 Sch 1 worksheet / Pub 525 /
  IRC Â§111).
- **KEY:** the SALT cap is NOT a compute constant â€” the worksheet reads the
  preparer-entered prior-year Sch A 5d/5e, so only the prior-year std-ded table is
  year-keyed (to the refund year = tax_year âˆ’ 1). 2024 verified; 2025 INTERIM
  (requires_human_review, re-pin from the 2026 worksheet ~Dec 2026).
- Taxable income-tax refund â†’ Sch 1 line 1; RE/PP + other recoveries â†’ Sch 1 line 8z.
  NO IRS AcroForm â€” a statement page (the Simplified Method precedent).
- Deployed export verified HTTP 200 (`lookup/STATE_REFUND/export/`); committed to
  tts-tax-app as canonical `server/specs/state_refund_spec.json` + 6 FA staged in
  `flow_assertions_1040_sr_pending.json` (active 1040 gate stays 153).
- Next (tts-tax-app): the build legs â€” seed (the 19 sr_* Taxpayer facts + a
  STATE_REFUND FormDef worksheet + serializer) â†’ compute (`compute_state_refund.py`
  â†’ Sch 1 L1 + L8z; runs BEFORE the first formula pass â€” it's INCOME, feeds 1040
  line 8 / AGI, NOT a credit) â†’ render (statement page) â†’ input â†’ diagnostics â†’
  assertions â†’ tag `1040-state-refund-complete`. This is the LAST post-sprint item.

## 2026-06-14 â€” Form 8863 (Education Credits, NEXT-UP #8) spec leg â€” SEEDED + EXPORTED âœ…
- **Ken approved the review walk in-session ("Looks good.")** â€” the Â§25A constants
  (AOTC 100%/25% to $4,000 / max $2,500 / 40% refundable $1,000; LLC 20% of
  $10,000 / max $2,000) + the shared phaseout ($90k/$180k ceiling, $10k/$20k
  divisor) + the per-student tiers + the 40% refundable split + the line-7
  kiddie-tax lockout (preparer checkbox, decision 2) + the full Credit Limit
  Worksheet (decision 3) + the MFS/dependent bars + the TY2026 Â§70606 defer.
- `load_1040_form_8863.py` + `check_8863_integrity.py` ALL CHECKS PASS
  (independent re-type of the Â§25A tiers + the shared phaseout + the LLC + the
  CLW + the 9 scenarios + the helper fns; loader & gate share no math). Guard
  verified REFUSING before the flip.
- Flipped READY_TO_SEED â†’ seeded: **FORM_8863** (7 facts / 7 rules / 32 lines /
  7 diagnostics / 9 scenarios / 12 cited links) + 6 flow assertions. **RS DB â†’53
  forms, FA â†’158.** All rules cited. 3 sources (i8863 / IRC Â§25A / Pub 970).
- CONSTANTS verified from the published 2025 f8863.pdf (9/23/25) / i8863 / Pub
  970 â€” all Â§25A STATUTORY, NOT inflation-indexed (identical 2024/25/26). AOTC
  L8 (40% refundable) â†’ 1040 L29; the nonrefundable education credit L19 (the
  Credit Limit Worksheet) â†’ Schedule 3 L3.
- **varchar(20) lesson â€” this time a diagnostic_id:** `D_8863_AOTC_INELIGIBLE`
  (22) overflowed FormDiagnostic.diagnostic_id â†’ renamed `D_8863_AOTC_INELIG`
  (18). Added a diagnostic_id length guard to the integrity gate (it already
  guarded rule_id). (`R-8863-AOTC-PHASEOUT` = exactly 20, fits.)
- Deployed export verified HTTP 200 (`lookup/FORM_8863/export/`); committed to
  tts-tax-app as canonical `server/specs/form_8863_spec.json` + 6 FA staged in
  `flow_assertions_1040_8863_pending.json` (active 1040 gate stays 147).
- Next (tts-tax-app): the 6 build legs â€” seed (a new **EducationStudent** model +
  RLS, the FORM_8863 FormDef + facts; decision 1) â†’ compute (`compute_8863.py`:
  the per-student AOTC + LLC + phaseout + the Credit Limit Worksheet â†’ Sch 3 L3 /
  1040 L29) â†’ render (f8863.pdf downloaded; per-student Part III copies) â†’ input â†’
  diagnostics â†’ assertions â†’ tag `1040-form-8863-complete`.

## 2026-06-14 â€” Form 8962 (Premium Tax Credit, NEXT-UP #7) spec leg â€” SEEDED + EXPORTED âœ…
- **Ken approved the review walk in-session ("Looks right")** â€” Table 2 applicable
  figure (interpolation, verified endpoints) + the 2024 FPL + Table 5 + line-5
  truncation + the monthly method + the iterative SEHI<->PTC + Parts 4/5 + the
  2026 RED-defer + the two requires_human_review flags (the full Table 2 lookup;
  the Pub 974 convergence).
- `load_1040_form_8962.py` + `check_8962_integrity.py` ALL CHECKS PASS (independent
  re-type of the FPL/Table-2/Table-5 math + the 5 helper fns + the 6 scenarios;
  loader & gate share no math). Guard verified REFUSING before the flip.
- Flipped READY_TO_SEED â†’ seeded: **FORM_8962** (17 facts / 13 rules / 38 lines /
  6 diagnostics / 6 scenarios / 15 cited links) + 6 flow assertions. **RS DB â†’52
  forms, FA â†’152.** All rules cited. 3 sources (i8962 / IRC Â§36B / Pub 974).
- CONSTANTS verified cell-by-cell from the 2025 i8962 PDF: line 5 trunc cap 401
  (400% cliff suspended 2025); Table 2 0/.02/.04/.06/.085 (+.0004/pt 150-300%,
  +.00025/pt 300-400%); Table 5 375/975/1,625 single & 750/1,950/3,250 other,
  no-limit >=400%; 2024 FPL 48-state 15,060/+5,380, AK 18,810/+6,730, HI 17,310/
  +6,190. Net PTC L26 -> Sch 3 L9; excess L29 -> Sch 2 L1a.
- Deployed export verified HTTP 200 (`lookup/FORM_8962/export/`); committed to
  tts-tax-app as canonical `server/specs/form_8962_spec.json` + 6 FA staged in
  `flow_assertions_1040_8962_pending.json` (active 1040 gate stays 141).
- rule_id length lesson (again): FormRule.rule_id is varchar(20) â€”
  R-8962-HOUSEHOLD-INCOME (23) / R-8962-APPLICABLE-FIGURE (24) overflowed; renamed
  -> R-8962-MAGI / R-8962-APPL-FIG.
- Next (tts-tax-app): the 6 build legs â€” seed (a new Form1095A model + RLS, mig
  0069; FORM_8962 FormDef + facts) â†’ compute (`compute_8962.py`: the MAGI helper +
  the monthly method + the SEHI iterative + Part 4/5 â†’ Sch 3 L9 / Sch 2 L1a; the
  BIGGEST build leg) â†’ render (f8962.pdf downloaded) â†’ input â†’ diagnostics â†’
  assertions â†’ tag `1040-form-8962-complete`.

## 2026-06-14 â€” Schedule E (Part I) + Form 8582 (NEXT-UP #6) spec leg â€” SEEDED + EXPORTED âœ…
- **Ken approved the review walk in-session ("Looks good.")** â€” the $25k/$12,500
  special allowance + the 50%Ã—($150k/$75kâˆ’MAGI) phaseout + the MFS amounts + the
  modified-AGI add-back list (NOT Â§199A) + the v1 simplified-bucket deviations
  (aggregate columns, no per-activity Parts IV/V, RE-pro RED, MFS-together $0,
  Â§280A vacation-home not applied, partial MAGI add-backs).
- `load_1040_schedule_e.py` seeds BOTH forms (the load_1040_schedule_d 3-form
  precedent); `check_schedule_e_8582_integrity.py` ALL CHECKS PASS (independent
  re-type of the Â§469(i) constants + the special-allowance helper + both forms'
  scenarios; loader & gate share no math). Guard verified REFUSING before the flip.
- Flipped READY_TO_SEED â†’ seeded: **SCHEDULE_E** (8 facts/4 rules/33 lines/4
  diag/4 scenarios/5 cited links) + **FORM_8582** (17 facts/6 rules/17 lines/6
  diag/7 scenarios/8 cited links) + 6 flow assertions. **RS DB 50â†’52 forms,
  FA 140â†’146.** All rules cited.
- **SUPERSESSION:** deleted the old non-standard `form_number="8582"` draft
  (generic R001/D001 ids, wrong line numbering â€” invented a CRD line 2). The
  re-authored form is the standard `FORM_8582`. The real 2025 structure: 1a-1d
  rental-RE-active / 2a-2d all-other-passive / 3 combine / Part II 4-9 special
  allowance / 10-11 total allowed.
- Deployed exports verified HTTP 200 (`lookup/SCHEDULE_E/export/` +
  `lookup/FORM_8582/export/`); committed to tts-tax-app as canonical
  `server/specs/{schedule_e,form_8582}_spec.json` + 6 FA staged in
  `flow_assertions_1040_sche_8582_pending.json` (active 1040 gate stays 135).
- rule_id length lesson: FormRule.rule_id is varchar(20) â€” `R-8582-SPECIAL-ALLOWANCE`
  (24) overflowed; renamed â†’ `R-8582-ALLOWANCE`.
- Next (tts-tax-app): the 6 build legs â€” seed (extend RentalProperty: address/
  active_participation/is_qjv/type-1-8/the two 1099-Qs, migration 0068; route the
  serializer/CRUD by form code) â†’ compute â†’ render â†’ input â†’ diagnostics â†’
  assertions â†’ tag `1040-schedule-e-8582-complete`.

## 2026-06-13 â€” Form 8880 (Saver's Credit, roster #9) spec leg â€” SEEDED + EXPORTED âœ…
- **Ken approved the scope walk in-session ("Looks good. Run it.")** â€” incl. the
  W-2 box-12 elective-deferral auto-derive (qualifying codes D/E/F/G/H/S/AA/BB/EE
  per owner; new tts-tax-app `W2Income.owner` field at the build leg). Authored +
  math-gated + flipped + seeded in one sitting: **RS DB 47 â†’ 48 forms, FA 123 â†’
  128.** `load_1040_form_8880.py` â€” FORM_8880 (11 facts / 5 rules / 18 lines /
  6 diagnostics D_8880_001..006 / 7 scenarios / 5 flow assertions FA-1040-8880-01..05
  / 2 new sources). Nonrefundable Â§25B credit â†’ Schedule 3 line 4 (already a
  direct-entry feeder).
- **Constants:** 2025 line-9 AGI tier table VERBATIM from f8880.pdf (pymupdf);
  2026 TOP cutoffs VERIFIED from the IRS 2026 COLA notice (MFJ $80,500 / HoH
  $60,375 / single-MFS $40,250) + the 2026 intermediate 50%/20% breakpoints
  carried from 2025 as an INTERIM (D_8880_003 re-pin ~Dec 2026 when the 2026 Form
  8880 publishes â€” the spine derived-2026 precedent). Per-person $2,000 cap + the
  50/20/10% statutory Â§25B.
- **`check_8880_integrity.py` ALL CHECKS PASS** â€” independent recompute of all 7
  scenarios (T1 MFJ 50%â†’2,000 / T2 single 20%â†’400 / T3 IRA+box12 capâ†’200 / T4
  distribution-reduces / T5 over-limitâ†’0 / T6 2026-top-cutoff / G1 student-excluded)
  + the tier table cross-checked both years.
- **HUMAN-REVIEW flag:** `IRS_2026_COLA_8880.requires_human_review=True` (the 2026
  intermediate breakpoints are interim). **Canonical `form_8880_spec.json` committed
  to tts-tax-app** + 5 FA-1040-8880 staged. Deployed export verified (HTTP 200).
  Next (tts-tax-app): build legs â€” seed (W2Income.owner + the 8880 facts + the
  pseudo-form), compute (box-12 derive + tier + credit â†’ Sch 3 L4), render, input,
  diagnostics, assertions.

## 2026-06-13 â€” NEXT-UP #1 (Simplified Method Worksheet) spec leg â€” SEEDED + EXPORTED âœ…
- **Ken approved the review walk in-session ("Looks good").** Flipped READY_TO_SEED
  + seeded: **RS DB 46 â†’ 47 forms, FlowAssertions 117 â†’ 123** (SIMPLIFIED_METHOD
  created, all rules cited). One seed-fix: `requires_human_review` is an
  AuthoritySource field, NOT an AuthorityExcerpt field â€” removed from the 4
  excerpt dicts (kept on the SMW source). **Deployed export verified** (HTTP 200,
  `lookup/SIMPLIFIED_METHOD/export/` â€” 14 facts / 6 rules / 11 lines / 6 diags /
  7 tests). **Canonical `simplified_method_spec.json` committed to tts-tax-app** +
  6 FA-1040-SM staged in `flow_assertions_1040_simplified_method_pending.json`.
  Next (tts-tax-app): build legs seed â†’ compute (supersede D_RET_001) â†’ render â†’
  input â†’ diagnostics â†’ assertions.
- `load_1040_simplified_method.py` (single form SIMPLIFIED_METHOD, the
  `load_1040_schedule_d.py` precedent). 14 facts / 6 rules / 11 lines (sm_1..sm_11) / 6
  diagnostics (D_SM_001..006) / 7 scenarios / 8 rule_links / 6 flow assertions
  (FA-1040-SM-01..06) / 2 new authority sources (Pub 575 + i1040 SMW).
- Replaces a LIVE tts-tax-app RED: **D_RET_001** (1099-R box-2a-blank-with-basis,
  the OPM/CSA-1099-R pattern). Computes the taxable pension via cost recovery â†’
  Form 1040 line 5b.
- **Constants VERIFIED vs IRS Pub 575 (2025):** Table 1 single-life (â‰¤55â†’360 /
  56-60â†’310 / 61-65â†’260 / 66-70â†’210 / 71+â†’160) + Table 2 joint-survivor by
  COMBINED age (â‰¤110â†’410 / 111-120â†’360 / 121-130â†’310 / 131-140â†’260 / 141+â†’210);
  the Nov-19-1996 (in-scope) / 1998 (Table 2) / 1987 (uncapped) boundary dates,
  statutory non-indexed. Ken's 7 scope decisions in tts-tax-app
  `server/specs/_next1_simplified_method_source_brief.md`.
- **`check_simplified_method_integrity.py` ALL CHECKS PASS** â€” independent retype
  of the 11-line worksheet + both tables (cell-by-cell cross-check) + the scope
  gates; load-bearing pins SM-T1 (single age 66 â†’ 210, taxable 21,600), SM-T2
  (joint combined 130 â†’ 310), SM-T3 (the cost cap binds â†’ balance 0 / D_SM_004),
  SM-T4 (partial 7-month, age 71 â†’ 160).
- **HUMAN-REVIEW flag:** the 11-line worksheet text is RECONSTRUCTED from the
  i1040 Simplified Method Worksheet + Pub 575 (the i1040 instructions page blocked
  verbatim auto-fetch); `IRS_2025_1040_SMW.requires_human_review=True`. Re-check
  the line text/order against the 2025 i1040 at Ken's walk. The ARITHMETIC is
  independently re-derived (the math gate is the real guard).
- **AWAITING Ken's review walk** â†’ flip READY_TO_SEED â†’ seed â†’ export canonical
  `simplified_method_spec.json` to tts-tax-app + stage assertions â†’ build legs
  (seed: new RetirementDistribution fields; compute: supersede D_RET_001; render:
  worksheet statement page; input; diagnostics; assertions). NOT seeded; RS DB
  unchanged. NOTE: RS root STATUS/MEMORY/DECISIONS still stale (Phase-0 note).

## 2026-06-13 â€” Topic 9 (Schedule D + 8949) spec-authoring leg â€” AUTHORED, math gate GREEN, NOT seeded
- `load_1040_schedule_d.py` authored (commit `f2c98f0`, 2,123 lines, READY_TO_SEED=False â€”
  guard verified refusing, zero DB writes): **SCHEDULE_D** (16 facts / 9 rules / 47 lines /
  11 diagnostics / 12 scenarios â€” the real 2025 face incl. the QOF question, per-box 8949
  totals pairwise A/G->1b..F/L->10, lines 4/5/11/12 direct-entry, carryover facts -> 6/14,
  DIV 2a -> 13, the line-16 -> 1040 7a routing + $3,000/$1,500 Â§1211(b) limit, the
  17/20/22 worksheet routing), **1040_SCHD_WS** (5/8/85/1/8 â€” sdtw_1..47 + clc_1..13
  carryover-OUT + w28_1..7 + u1250_1..18, all transcribed verbatim from i1040sd 2025),
  **8949 RE-AUTHOR** (29/5/26/5/6 â€” the 12-box A-L system incl. 1099-DA digital assets,
  the 18-code column-(f) table as adj_code_* data-list facts, Exception-2 summary rows,
  CapitalTransaction surface; `_retire_stale_8949` drops the thin 1120-S-era draft by
  keep-set; entity_types stays multi-entity). 12 flow assertions FA-1040-SCHD-01..12.
- Primary sources fetched + dumped same day (tts-tax-app server/.scratch/): f1040sd /
  i1040sd (16pp, all four worksheets) / i8949 (13pp, the code table) / f8949 (local copy
  confirmed = the 2025 12-box revision). 4 new AuthoritySources + RP_2025_32 Â§4.01 excerpt.
- **`check_topic9_integrity.py` ALL CHECKS PASS**: independent retype of the netting/CLC/
  28%/1250/SDTW math + the Tax Table/TCW convention; every scenario pin recomputed
  (SDTW-T1 pins 25% partial-bind 675 / SDTW-T2 28%-cap-no-bind L43=0 / SDTW-T3 28% binds
  28,000 / SDTW-T4 the 1==16 skip + table 3,605); **the SDTW==QDCGT invariant swept over
  13 cases x both years x 5 statuses**; constants cross-checked cell-by-cell incl.
  line-19 == the 24%-bracket tops BOTH years (2026 derived from RP 2025-32 Â§4.01 â€”
  walk item 1; HOH $201,750 vs single/MFS $201,775).
- **Sibling supersession edits authored (NOT run â€” they apply at the post-walk re-run):**
  `load_1040_intdiv_qdcgt.py` â€” D_INTDIV_001/002 retired (+ `_retire_topic9_superseded`
  deletion helper; ID-T3/G1/G2 + FA-1040-INTDIV-05 re-pointed to the Schedule-D path;
  R-QDCGT-GATE + WS3 gain the Sch-D branch). `load_1040_schedule_c.py` â€” 8995 L12 gains
  the Schedule D net-capital-gain component (i8995 verbatim); D_8995_002 retired from the
  keep-set (deleted on re-run).
- 10 requires_human_review walk items in the loader docstring. Next: Ken's review walk ->
  flip -> seed -> export canonical specs + staged assertions -> tts-tax-app build legs.

## 2026-06-13 â€” Topic 9 SEEDED on Ken's approval ("Looks good. Go.")
- `READY_TO_SEED` flipped -> `load_1040_schedule_d` run: SCHEDULE_D (16f/9r/47L/11d/12s)
  + 1040_SCHD_WS (5f/8r/85L/1d/8s) created; **8949 re-authored** (`_retire_stale_8949`
  deleted 38 stale 1120-S-era rows -> 29f/5r/26L/5d/6s, all cited); 12 FA-1040-SCHD.
  **RS DB 44->46 forms, FlowAssertions 105->117.**
- Sibling loaders re-run to apply the supersession edits: `load_1040_intdiv_qdcgt`
  retired **D_INTDIV_001/002** (`_retire_topic9_superseded`; deployed export confirms â€”
  diags now 003-010); `load_1040_schedule_c` retired **D_8995_002** (deployed export
  confirms â€” diags 001/003/004/005). Both deployed and round-trip-verified.
- tts-tax-app committed canonical `{schedule_d,1040_schd_ws,8949}_spec.json` + 12 staged
  assertions (`272aeee`). Amended intdiv/8995 canonical re-export DEFERRED to the
  Topic 9 compute leg (the spec-driven scenario tests read those files â€” re-export in
  lock-step with route_line_16 / compute_8995_db). Next: tts-tax-app build legs.

## 2026-06-12 c â€” 8995 L11 sourcing amended on Ken's approval (subtract Sch 1-A 13b)

- At the tts-tax-app compute leg the engine flagged that the 8995 spec sources L11
  (taxable income before QBI) as "1040 L11 âˆ’ L12" verbatim â€” it did NOT subtract the
  OBBBA Schedule 1-A line-13b deduction, although taxable income now includes 13b.
  **Ken ruled in-session: subtract 13b** (L11 = 1040 L11 âˆ’ L12 âˆ’ L13b â€” every non-QBI
  deduction comes out before the QBI income limitation). Affects the L14 limitation
  cap and the 8995-vs-8995-A threshold boundary on senior/tips/overtime QBI returns.
- `load_1040_schedule_c.py` updated in 3 places (the `qbi_taxable_income_before_qbi`
  fact note, the R-8995-L13-L14 formula + description, the line-11 line_map
  description) and RE-RUN idempotently â€” **DB counts unchanged** (44 forms, FA 105;
  update-in-place). Deployed export verified (fact/rule/line carry the 13b text;
  counts 13/8/21/5/7). Canonical `8995_spec.json` re-exported + committed in
  tts-tax-app; engine (`compute_8995_db`) + diagnostic (D_8995_001) + tests updated
  the same sitting.

## 2026-06-12 b â€” Topic 8 (Sch C + SE + 8995 re-author + 8959) REVIEWED + SEEDED on Ken's approval
- Review walk in-session: Ken **APPROVED as authored**. The 4 `requires_human_review`
  walk items accepted as recommended: (1) 2026 MFS 8995 threshold $201,775 as
  published (RP 2025-32 Â§4.26 rounding artifact, $25 above 'other' â€” diagnostic
  boundary only); (2) multi-business QBI reduction (Â½-SE/SEHI/retirement) allocated
  **pro-rata by net SE earnings**; (3) 8995 L12 net capital gain = 1040 L3a +
  cap-gain distributions in v1, net-LT-gain added when Schedule D lands +
  D_8995_002 warning; (4) QBI loss carryforward **supported** in v1. RED-defer
  enumeration confirmed.
- `READY_TO_SEED` flipped â†’ `load_1040_schedule_c` run clean (no en-route fixes).
  **Created SCHEDULE_C** (24 facts/9 rules/56 lines/7 diags/7 scenarios) + **SCHEDULE_SE**
  (17/12/24/4/5) + **8959** (13/6/24/4/5); **8995 RE-AUTHORED** (13/8/21/5/7) â€” the
  `_retire_stale_8995` step deleted **28 stale stub rows** (10 facts / 11 rules / 1
  line / 3 diags / 3 tests + cascading RuleAuthorityLinks). **14 flow assertions.**
  6 new authority sources + RP 2025-32 Â§4.26 excerpt, 100% cited. **RS DB: 41 â†’ 44
  forms; FlowAssertions 91 â†’ 105.** Math gate re-run green pre-seed.
- Deployed exports verified (`lookup/SCHEDULE_C|SCHEDULE_SE|8995|8959/export/` HTTP
  200 â€” counts round-trip 24/9/56/7/7 Â· 17/12/24/4/5 Â· 13/8/21/5/7 Â· 13/6/24/4/5; 8995
  re-author pins survive: R-8995-L15 present, stub R001 / `qualified_business_income`
  GONE, real 17-line face incl. 1i-1v / 17). Committed to tts-tax-app as canonical
  `server/specs/{schedule_c,schedule_se,8995,8959}_spec.json` + the 14 assertions
  STAGED in `flow_assertions_1040_topic8_pending.json` (active 1040 gate untouched at
  86; flow gate 108 passed â€” no tts-tax-app code touched).
- NEXT: tts-tax-app build legs (seed â†’ compute â†’ render â†’ input â†’ diagnostics â†’
  assertions per form), starting with build leg 1 â€” the **multi-business Schedule C FK
  model** (proprietor=taxpayer|spouse) + Schedule SE/8995/8959 models + the
  `seed_schedule_c`/`seed_schedule_se`/`seed_8995`/`seed_8959` commands + the
  f1040sc/f1040sse/f8995(have)/f8959 manifest entries.

## 2026-06-12 â€” Topic 8 (Schedule C + SE + 8995 re-author + 8959) specs AUTHORED + math gate GREEN (READY_TO_SEED=False)
- `specs/management/commands/load_1040_schedule_c.py` authored (Sprint Topic 8 /
  NEXT-UP #1), commit `aac4a38`. ONE idempotent command (the `load_1040_eic.py`
  4-form precedent) creating FOUR TaxForms from the Topic 8 source brief
  (tts-tax-app `server/specs/_topic8_schedulec_source_brief.md`), 100% cited:
  - **SCHEDULE_C** (24 facts / 9 rules / 56 lines / 7 diags / 7 scenarios / 10
    links): Parts I-V incl. Part III COGS (Decision 1); line-30 simplified home
    office (Decision 2 â€” min(sqft,300)x$5, gross-income limited to line 29, no
    carryover); per-business (Decision 3); line 13 -> 4562 engine; line 31 ->
    Sch 1 L3 + Sch SE L2. RED-defers: statutory employee, line 32b (6198), 8829.
  - **SCHEDULE_SE** (17/12/24/4/5/13): Part I standard method, per proprietor;
    year-keyed SS wage base (176,100 / 184,500); L12 -> Sch 2 L4, L13 -> Sch 1
    L15 (existing EIC Worksheet-B + 8812 feeder); L6 -> 8959 L8. Part II
    optional + church = RED-defer.
  - **8995** RE-AUTHORED (13/8/21/5/7/10): retires the wrong stub (R001-R005 /
    D001-D003 / lines 1-8 / 3 tests via `_retire_stale_8995`) and writes the
    real 17-line face â€” per-business QBI reduced by 1/2-SE/SEHI/SE-retirement,
    REIT/PTP component, income limitation -> 1040 L13a; year-keyed threshold
    (above -> 8995-A RED-defer).
  - **8959** (13/6/24/4/5/7, Decision 4): Part I wages + Part II SE (threshold
    REDUCED BY Medicare wages) -> Sch 2 L11; Part V withholding -> 1040 L25c;
    non-indexed thresholds; Part III RRTA RED-defer.
  - **14 flow assertions** (FA-1040-SCHC-01..04, SCHSE-01..03, 8995-01..03,
    8959-01..03, TOPIC8-01 the Sch C -> Sch SE L6 -> 8959 L8 chain).
  - 6 NEW authority sources (Sch C face + i1040sc, Sch SE face, 8995 face +
    re-authored i8995, 8959 face, Topic 751/SSA) + RP 2025-32 Â§4.26 excerpt on
    the EXISTING RP_2025_32. 4 `requires_human_review` WALK ITEMS flagged in the
    module docstring + rule descriptions: (1) 2026 MFS 8995 threshold $201,775 is
    $25 above 'other' $201,750; (2) multi-business QBI allocation of
    1/2-SE/SEHI/retirement (pro-rata default); (3) net-cap-gain / Schedule-D
    deferral for 8995 L12; (4) QBI loss carryforward in/out.
  - Year-keyed: SE_WAGE_BASE (176,100/184,500), QBI_THRESHOLDS (per status, both
    years). Statutory/non-indexed (NOT year-keyed): SE 92.35/12.4/2.9/50 + $400;
    8959 thresholds + 0.9%/1.45%; 20% QBI rate; home-office $5/300.
- `check_topic8_integrity.py` authored + GREEN (commit `338a373`, the math gate
  before Ken's walk). Carries its OWN re-typed constants + independent
  recomputations of Schedule SE Part I (incl. the W-2-SS-wage cap), the Schedule
  C gross-income/COGS/simplified-home-office chain, the 8995 QBI
  reduction+income-limitation, and the 8959 reduced-threshold math; every
  scenario (SC-T1..T7 / SE-T1..T5 / 8995-T1..T7 / 8959-T1..T5) recomputed and
  matched; loader module constants cross-checked cell-by-cell; load-bearing pins
  (SS cap binds; year-keying load-bearing; 8959 line 11 = threshold - Medicare
  wages; QBI income limit binds; home-office gross-income limit). Found + fixed
  one loader slip (SE-T5 L13 2119.43 -> 2119.44 ROUND_HALF_UP) + one structural
  input typo (8959 ENGAGE). **ALL CHECKS PASS.**
- **Loader REFUSES (READY_TO_SEED=False, "all populated", CommandError, zero DB
  writes). RS DB UNCHANGED (still 41 forms; SCHEDULE_C/SCHEDULE_SE/8959 absent;
  8995 stub NOT yet replaced â€” the re-author waits for the flip).**
- NEXT: Ken's review walk (in-session) â†’ on approval flip `READY_TO_SEED=True` â†’
  seed (re-authors 8995) â†’ verify deployed exports â†’ commit canonical
  `server/specs/{schedule_c,schedule_se,8995,8959}_spec.json` to tts-tax-app +
  stage flow assertions â†’ build legs (seed â†’ compute â†’ render â†’ input â†’
  diagnostics â†’ assertions per form).

## 2026-06-11 g â€” Topic 7 (EIC + 8867/8862) specs AUTHORED + math gate GREEN (READY_TO_SEED=False)
- `specs/management/commands/load_1040_eic.py` authored (Sprint Topic 7), commit
  `48e1fef`. Creates FOUR TaxForms from the Topic 7 source brief (tts-tax-app
  `server/specs/_topic7_eic_source_brief.md`), the `load_1040_retirement.py`
  precedent, 100% cited:
  - **1040_EIC** (computational pseudo-form): 33 facts / 10 rules / 18 lines /
    16 diagnostics / 16 scenarios / 16 rule_links. Step-5 earned income,
    Worksheet A (non-SE) + mainstream Worksheet B (SE: Sch1 L3 net SE âˆ’ Sch1 L15
    Â½-SE-tax), the EIC Table $50-bracket midpointÃ—rate ROUND_HALF_UP lookup, the
    lower-of-AGI/earned-income rule, the Pub 596 Worksheet-1 investment-income
    limit, the Rules-for-Everyone + childless eligibility gates â†’ 1040 line 27a.
    **YEAR-KEYED `EIC_PARAMS`** (both years, each verified independently â€” unlike
    Topic 5's statutory non-indexed constants).
  - **SCHEDULE_EIC** (7/1/7/1/2/1): model-driven per-child face from Dependent rows.
  - **8867** (16/1/12/2/3/1) + **8862** (6/1/6/1/2/1): data-map faces, no compute.
  - **9 flow assertions** FA-1040-EIC-01..09 (27a feeder; the year-keyed Â§32
    constants_check; the midpoint-table convention; lower-of rule; investment-income
    gate; childless age band; combat-pay election; QSS=other column; the
    eligibility-gate truth table).
  - NEW sources: Pub 596, Schedule EIC, Form 8867, Form 8862. NEW excerpts on the
    EXISTING `RP_2024_40`/`RP_2025_32` (Â§2.06 EIC, distinct from intdiv's Â§2.03/Â§4.03
    QDCGT excerpts) + `IRS_2025_1040_INSTR` (Worksheets A/B + EIC Table).
- `check_eic_integrity.py` authored + GREEN (commit `5051f81`, the math gate before
  Ken's walk). Carries its OWN re-typed Â§32 tables + EIC Table evaluator (not
  imported from the loader): loader `EIC_PARAMS` cross-checked cell-by-cell both
  years; Â§32 internal reconciliation within $1 (covers the published TY2026 0-QC
  $664 vs 663.42); the i1040gi midpoint pin 2,475â†’842 (841.5 ROUND_HALF_UP, not
  truncate); lower-of binds T3â†’1,663; exact phaseout T2â†’389; year-keying
  load-bearing (TY2026 3+ 8,231 â‰  TY2025 8,046); MFJ-vs-other column; combat-pay
  election; Worksheet-B SE; the 5 RED-gate fixtures; FA-02/06/08 constants. ALL PASS.
- **Loader REFUSES (READY_TO_SEED=False, "all populated", exit 1, zero DB writes).
  RS DB UNCHANGED (still 37 forms; 1040_EIC/SCHEDULE_EIC/8867/8862 absent).**
- **Ken's review walk â€” APPROVED in-session.** The one open item (Worksheet-B
  SE-component sourcing) confirmed = `eic_se_net_earnings` â† Sch 1 L3 (net SE) /
  `eic_se_half_deduction` â† Sch 1 L15 (Â½-SE-tax) per the DoD "Schedule 1
  flowed-or-direct, Schedule C compute NOT required".
- **Flipped `READY_TO_SEED=True` + seeded** (commit `00a550c`): `load_1040_eic`
  created 1040_EIC (33/10/18/16/16) + SCHEDULE_EIC (7/1/7/1/2) + 8867 (16/1/12/2/3)
  + 8862 (6/1/6/1/2), 4 new authority sources + Â§2.06 EIC excerpts on
  RP_2024_40/RP_2025_32 + Worksheet/EIC-Table excerpts on the 1040 instructions,
  **9 flow assertions**. All 4 forms 100% cited. **RS DB: 37 â†’ 41 forms;
  FlowAssertions 82 â†’ 91.** Math gate re-run green pre-seed.
- Deployed exports verified (`lookup/1040_EIC|SCHEDULE_EIC|8867|8862/export/` HTTP
  200 â€” counts round-trip + pins EIC-T4 842 / EIC-T9 8231). Committed to tts-tax-app
  as canonical `server/specs/{eic,schedule_eic,8867,8862}_spec.json` + the 9
  assertions STAGED in `flow_assertions_1040_eic_pending.json` (active 1040 gate
  untouched at 77; flow gate 99 passed).
- NEXT: tts-tax-app build legs (seed â†’ compute â†’ render â†’ input â†’ diagnostics â†’
  assertions), starting with build leg 1 â€” Dependent + Taxpayer additive migrations
  (EIC reuses Dependent, no new doc model) + seed_1040_eic/schedule_eic/8867/8862 +
  the f1040sei/f8867/f8862 manifest entries.

## 2026-06-11 f â€” Topic 5 (Retirement) REVIEWED + SEEDED on Ken's approval
- Review walk in-session: Ken **approved** (source citations + SS Benefits
  Worksheet transcription + scope already confirmed). Two walk outcomes:
  (a) **TY2026 Â§86/5329 constants confirmed NON-INDEXED** â€” SS base/second-tier
  ($25k/$32k, $9k/$12k) and the 50%/85% rates are statutory Â§86 (no inflation
  adjustment cross-reference), and the Â§72(t) 10%/25% rates are statutory; RP
  2025-32 adjusts none â€” same pattern as Schedule 1-A. So NO `_constants_for_year`
  in this topic. (b) **R-RET-CODE J-wording tightened** â€” the formula listed
  "J (10%, RED if box2a blank)" among early codes; J/T are OUT of v1 and always
  RED, so the EARLY clause now lists only `1 (10%), S (25%)` and J/T moved to the
  RED-UNSUPPORTED clause; D_RET_003 condition reworded to "{v1 set} (J and T OUT
  of v1 -> always RED)". No math impact (no J/T scenario). Integrity check re-run
  green after the edit.
- `READY_TO_SEED` flipped â†’ `load_1040_retirement` run clean: **Created
  1040_RETIREMENT** (25 facts/8 rules/24 lines/7 diags/18 scenarios) + **5329**
  (3/3/4/1/3), 16 authority links (100% cited), 2 new excerpts on
  IRS_2025_1040_INSTR, **7 flow assertions**. **RS DB: 35 â†’ 37 forms,
  FlowAssertions 75 â†’ 82.**
- Deployed exports verified (`lookup/1040_RETIREMENT|5329/export/` HTTP 200 â€”
  counts 25/8/24/7/18 + 3/3/4/1/3 survive; SS-3 6b=17,000 / SS-4 15,350 /
  SS-5 8,500 / RET-T4 4b=0 / RET-5329-3 line4=2,500 / F5329-T2 1,200 all
  round-trip). Committed to tts-tax-app as canonical `server/specs/
  retirement_spec.json` + `5329_spec.json`; the 7 assertions STAGED in
  `flow_assertions_1040_retirement_pending.json` (active 1040 gate untouched at
  70; flow gate still 92 passed).
- NEXT: tts-tax-app build legs (seed â†’ compute â†’ render â†’ input â†’ diagnostics â†’
  assertions), starting with the new **RetirementDistribution** model + the
  SSA-1099 return-level fields + f5329 manifest/field-map.

## 2026-06-11 e â€” Topic 5 integrity check written + green (math gate before Ken's walk)
- `check_retirement_integrity.py` authored (RS root; mirrors
  `check_intdiv_integrity.py`/`check_sch123_integrity.py`). Validates the authored
  lists WITHOUT touching the DB, then INDEPENDENTLY recomputes every numeric
  scenario from its OWN transcription:
  - **SS Benefits Worksheet (18 lines)** â€” full re-implementation of i1040gi p.31
    incl. both STOP conditions (line 7, line 9) and the MFS-lived-with-spouse
    short-circuit; verifies SS-1..5 line-by-line (every authored `ws_*` +
    6a/6b), plus the FA-RET-05 invariant (6b â‰¤ 85%Ã—WS1 and â‰¤ WS1) on each.
  - **1099-R aggregation** â€” RET-T1..5 (4a/4b IRA, 5a/5b pension, 25b withholding;
    rollover/QCD per-doc floor; rollover/QCD literal-flag consistency).
  - **Form 5329 Part I** â€” RET-5329-1..3 (doc-driven early amount + 10%/25%) and
    F5329-T1..3 (direct facts); the direct-to-Sch-2 generation gate (R-5329-03).
  - **RED-gate fixtures** â€” RET-G1..5 each verified to actually satisfy its
    diagnostic condition (D_RET_001/002/003/004/006).
  - **Load-bearing pins** â€” 85% cap binding in SS-3; MFS branch â‰  normal path;
    SIMPLE 25% â‰  10%; FA-1040-RET-06 constants_check matches the independent Â§86
    values (25k/32k, 9k/12k, 0.50/0.85, years [2025,2026]); J excluded from v1.
  - Structural checks (dup keys/ids/lines, uncited rules, dangling links,
    inputs-are-facts) all clean.
- **ALL CHECKS PASS.** Loader guard still REFUSES (READY_TO_SEED=False, exit 1,
  zero DB writes); **RS DB UNCHANGED (35 forms; 1040_RETIREMENT/5329 absent).**
- ONE packet item surfaced for the walk: R-RET-CODE's formula lists
  "J (10%, RED if box2a blank)" as an early code, but the Ken-confirmed v1 set
  and D_RET_003 exclude J entirely (always RED). Wording to reconcile â€” no math
  impact (no J scenario).
- NEXT: Ken's review walk â†’ on approval flip READY_TO_SEED â†’ seed â†’ verify â†’
  export canonical specs + stage flow assertions â†’ tts-tax-app build legs.

## 2026-06-11 d â€” Topic 5 (Retirement Income) specs AUTHORED, READY_TO_SEED=False
- `specs/management/commands/load_1040_retirement.py` authored (Sprint Topic 5).
  Creates TWO TaxForms: **1040_RETIREMENT** (pseudo-form: ~33 facts [full 1099-R
  box surface + SSA-1099 + rollover/QCD/5329-linkage], 12 rules, 27 lines [4a/4b/
  5a/5b/6a/6b aggregation + the 18-line SS Benefits Worksheet], 7 diagnostics,
  14 scenarios) and **5329** (real face Part I: 3 facts, 3 rules, 4 lines, 1
  diagnostic, 3 scenarios). **7 flow assertions** (FA-1040-RET-01..07: 4a/4b &
  5a/5b rosters, 25b extension, 5329 line-4 rate, SS 6b=min(WS16,WS17)+85% cap,
  the statutory SS constants both years, the RED-gate truth table). **4 new
  authority sources** (Form 1099-R, i1099r Table 1 distribution codes, Form 5329,
  i5329 exception list) + 2 new excerpts on IRS_2025_1040_INSTR (the SS worksheet
  verbatim + lines 4a/4b/5a/5b rollover/QCD literals). Rule links 100% cited.
- Sources fetched + text-extracted the same day (tts-tax-app `server/.scratch/`:
  f1099r/i1099r/f5329/i5329-2025.pdf + dumps; SS worksheet from the existing
  i1040gi-2025.pdf p.31). Consolidated brief committed at tts-tax-app
  `server/specs/_topic5_retirement_source_brief.md`.
- **Ken's 5 scope decisions confirmed in-session 2026-06-11** and encoded: v1
  distribution-code set (1,2,3,4,7,8,9,B,D,G,H,Q,S,Y + IRA checkbox; rest RED);
  5329 exceptions 01-12+19 (â‰¥13/99 RED); direct-to-Sch-2 shortcut; rollover/QCD
  preparer-entered; TY2026 statutory constants to confirm at the walk.
- **No year-keyed constants** (SS Â§86 thresholds + 5329 10%/25% are statutory
  non-indexed â€” same both years, unlike Topic 3's breakpoints).
- Verified: `py_compile` clean; `manage.py load_1040_retirement` REFUSES
  (READY_TO_SEED=False, "all populated", exit 1, zero DB writes â€” imports + guard
  + roster all valid). **RS DB UNCHANGED (still 35 forms).**
- NEXT: (1) write `check_retirement_integrity.py` (independent recompute of the
  SS worksheet + 5329 scenarios â€” the math-verification gate before the walk);
  (2) Ken's review walk; (3) on approval flip â†’ seed â†’ verify â†’ export canonical
  `retirement_spec.json` + `5329_spec.json` to tts-tax-app + stage flow
  assertions; (4) tts-tax-app build legs.

## 2026-06-11 c â€” Spine bridge retired (Topic 3 compute leg, Ken-approved narrowing)
- `load_1040_spine.py` edited per the approved D_1040_001-narrowing plan
  (PM #11 pattern, new explicit `_retire_bridge_artifacts` step mirroring
  the Session-14 stub retirement): **R-TAX-07 rule (+1 authority link),
  D_1040_001 diagnostic, DG-1 scenario, and FA-1040-SPINE-15 deleted**;
  R-TAX-01 routing now names the QDCGT worksheet for supported
  preferential-rate paths + the still-blocked overrides
  (D_INTDIV_001..004 / D_1040_003/004); facts 3a/3b/7a + lines 3a/3b
  (now `calculated`) /7a/16 notes updated to the computed-feeder reality.
- `run_spine_check.py` clean (44 rules / 16 diags / 32 scenarios / 15
  assertions, 0 uncited, no dangling links) â†’ loader re-run idempotent
  against the deployed DB (retirement report: rules+links=2, diags=1,
  scenarios=1, FAs=1). **RS DB: 35 forms, FlowAssertions 75; 1040 FA
  export 61 â†’ 60 (SPINE-15 gone, verified).**
- Deployed `lookup/1040/export/` semantically diffed vs the old canonical
  spec: ONLY the intended removals + the 8 narrowed-note items â€” committed
  to tts-tax-app as the new canonical `server/specs/1040_spine_spec.json`.

## 2026-06-11 b â€” 1040_INTDIV / SCH_B seeded on Ken's approval
- Review packet walked with Ken in-session (six judgment items incl. the
  WS18/WS21 half-up whole-dollar rounding, both years' breakpoint tables,
  aggregation rosters, diagnostics severities, the 21 scenarios, the
  D_1040_001-narrowing plan). **Approved as authored.**
- `READY_TO_SEED` flipped â†’ `load_1040_intdiv_qdcgt` run clean (no en-route
  fixes). Seeded: 1040_INTDIV (55 facts/17 rules/30 lines/10 diags/15
  scenarios), SCH_B (5/6/10/7/6), 12 flow assertions, 4 new sources + 5 new
  excerpts on existing, 37 links (100% cited). **RS DB: 35 forms,
  FlowAssertions 76.**
- Deployed exports verified (`lookup/1040_INTDIV|SCH_B/export/` â€” counts +
  both years' breakpoints + the ID-Q9 248 rounding pin + SB-T1 2,375 tie all
  survive the round trip). Committed to tts-tax-app as canonical
  `server/specs/intdiv_spec.json` / `sch_b_spec.json` (`ebfe2d1`).
- `/api/flow-assertions/export/?entity_type=1040` now returns **61** (49 +
  12 INTDIV/SCHB). The 12 are STAGED in tts-tax-app
  (`flow_assertions_1040_intdiv_pending.json`) â€” wired leg by leg.
- Next: tts-tax-app build legs (seed â†’ compute â†’ render â†’ input â†’
  diagnostics â†’ assertions; D_1040_001 narrows via load_1040_spine edit at
  the compute leg).

## 2026-06-11 â€” Topic 3 specs authored (Interest, Dividends & QDCGT), READY_TO_SEED=False
- `specs/management/commands/load_1040_intdiv_qdcgt.py` authored: creates TWO
  TaxForms in one idempotent command. **1040_INTDIV (pseudo-form): 55 facts /
  17 rules / 30 lines / 10 diagnostics / 15 scenarios â€” 1099-INT/DIV document
  facts + aggregation to 1040 2a/2b/3a/3b/7a + 25b extension + the full
  25-line QDCGT worksheet. SCH_B: 5 facts / 6 rules / 10 lines / 7
  diagnostics / 6 scenarios. 12 flow assertions (FA-1040-INTDIV-01..10,
  FA-1040-SCHB-01..02), 4 new authority sources (Sch B face + instructions,
  1099-INT, 1099-DIV), 5 new excerpts on existing sources (QDCGT worksheet
  verbatim + Exception 1 + line sources on IRS_2025_1040_INSTR; Â§2.03/Â§4.03
  breakpoints on RP_2024_40/RP_2025_32), 37 rule links (100% cited).**
- Sources: 2025 f1040sb downloaded into the tts-tax-app manifest (SHA
  recorded); i1040sb (3pp), i1040gi pp.25-26/31/33/37-38, 1099-INT/DIV
  Rev. 1-2024 faces, RP 2024-40 Â§2.03 + RP 2025-32 Â§4.03 all transcribed
  positionally the same session (dumps in tts-tax-app server/.scratch/).
- **Year-keyed constants (the only ones):** QDCGT WS6/WS13 breakpoints.
  TY2025 triple-verified (rev proc + worksheet face + prior capture);
  TY2026 from RP 2025-32 Â§4.03 â€” incl. the trap that WS13 single â‰  MFS
  (533,400 vs 300,000) while WS6 single == MFS.
- **Six judgment items flagged for Ken** (module docstring + rule
  descriptions): ABP box-11/12 default subtraction, per-doc tax-exempt
  floor, box-10 market-discount inclusion, WS18/WS21 half-up whole-dollar
  rounding (pinned by scenario ID-Q9 247.50â†’248), the Exception-1
  preparer-assertion fact, 3a override convention for holding-period
  exceptions.
- **Spine supersession documented:** R-TAX-07/D_1040_001 bridge NARROWS to
  D_INTDIV_001/002/003/004 (Sch D required / unasserted 2a / 8814 / 2555);
  spine R-PAY-02 25b roster extends to DIV box 4; 1040 2a/2b/3a/3b become
  computed feeders. D_1040_001 retires at the build leg via spine-loader
  edit (PM #11 pattern) on Ken's approval.
- `check_intdiv_integrity.py` (RS root): structural checks + INDEPENDENT
  recomputation of every scenario â€” full 25-line worksheet from its own
  bracket/breakpoint transcription (2026 MFJ uppers verified against the
  Ken-blessed compute.py table), boundary-pair checks, rounding-pin
  load-bearing check, cross-fixture SB-T1 == ID-T1 roster tie. ALL CHECKS
  PASS.
- Guard verified: `manage.py load_1040_intdiv_qdcgt` refuses with
  CommandError while READY_TO_SEED=False. No DB writes this session.
- Next: Ken's review walk (packet in the tts-tax-app session) â†’ flip â†’
  seed â†’ export 1040_INTDIV/SCH_B specs + flow assertions â†’ build legs.

## 2026-06-10 PM #12b â€” SCH_1/SCH_2/SCH_3 seeded on Ken's approval
- Review packet walked with Ken in-session (totals formulas incl. the Sch 2
  line-20 exclusion, sign conventions, diagnostics severities, 13 scenarios,
  8812 placeholder re-pointing by semantic content). **Approved as authored.**
- `READY_TO_SEED` flipped â†’ `load_1040_sch123` run. One fix en route: the
  IRC_62 excerpt carried `requires_human_review` â€” **AuthorityExcerpt has no
  such field (source-level only, re-learned from PM #5)**; moved the flag into
  summary_text. Atomic transaction = no partial writes from the failed run.
- Seeded: SCH_1 (69 facts/10 rules/63 lines/6 diags/6 scenarios), SCH_2
  (53/10/45/5/4), SCH_3 (34/8/33/3/4), 13 flow assertions, 36 links (100%
  cited). **RS DB: 33 forms, FlowAssertions 64.**
- Deployed exports verified (`lookup/SCH_1|SCH_2|SCH_3/export/` â€” counts match,
  R-S2-05 "EXCLUDES L20" + S2-T2 1884 + S1-T2 -21000 survive the round trip).
  Committed to tts-tax-app as canonical `server/specs/sch_{1,2,3}_spec.json`.
- `/api/flow-assertions/export/?entity_type=1040` now returns 49 (13 CTC +
  7 SCH1A + 16 SPINE + 13 SCH123). The 13 are STAGED in tts-tax-app
  (`flow_assertions_1040_sch123_pending.json`) â€” wired leg by leg.
- Export-format note: spec export top-level keys are `metadata` / `facts` /
  `rules` / `line_map` / `diagnostics` / `tests` / `authority_sources` /
  `state_conformity` (no `form` / `lines` keys).

## 2026-06-10 PM #12 â€” Schedules 1/2/3 specs authored (Sprint Topic 2), READY_TO_SEED=False
- `specs/management/commands/load_1040_sch123.py` authored: creates THREE TaxForms
  (SCH_1 / SCH_2 / SCH_3, FED TY2025 v1) in one idempotent command.
  **SCH_1: 69 facts / 10 rules / 63 lines / 6 diagnostics / 6 scenarios.
  SCH_2: 53 / 10 / 45 / 5 / 4. SCH_3: 34 / 8 / 33 / 3 / 4.
  13 flow assertions (FA-1040-SCH1-01..04, SCH2-01..05, SCH3-01..04).
  4 new authority sources (3 form faces + IRC_62), 36 rule-authority links
  (100% cited).**
- Sources: 2025 f1040s1/f1040s2/f1040s3 downloaded fresh from irs.gov into
  tts-tax-app's manifest (SHA256 recorded) and transcribed positionally with
  pymupdf the same session. Schedule 3 (2025) is a SINGLE page â€” manifest
  corrected. Schedule 2 (2025) adds EPE recapture lines 1d/1e/1f/19 (Form 4255).
- Aggregation-form scope: every line direct-entry; computed lines are the face
  sums only (S1: 9/10/25/26 Â· S2: 1z/3/7/18/21 Â· S3: 7/8/14/15). NO year-keyed
  constants exist on these forms â€” the TY2026 faces must be re-verified on
  release (tracker note).
- Load-bearing subtleties encoded: **Sch 2 line 20 (965 installment) is NOT in
  the line-21 sum** (scenario S2-T2 pins 1,884 not 3,884); Sch 1 8a/8d/8s are
  NEGATIVE entries (parentheses); 'combine' lines 10/9 allow negatives (loss
  year scenario pins -21,000); Sch 3 6l (8978) is signed; reserved lines
  S1.22 / S2.10 / S3.6e police-checked.
- Spine supersession documented per rule: 1040 lines 8/10/17/20/23/31 become
  COMPUTED feeders from S1.10/S1.26/S2.3/S3.8/S2.21/S3.15, retiring the spine's
  six direct-entry schedule facts. 8812 placeholder re-pointing (se_tax_total,
  additional_medicare_tax_amount, other_employment_taxes, excess_ss_rrta_withheld,
  deductible_se_tax_half, schedule_3_pre_ctc_credits_total) flagged for Ken in
  the review walk â€” the 8812 spec's Sch 2/3 line references predate the 2025
  renumbering.
- `check_sch123_integrity.py` (RS root): pre-seed checker â€” duplicate ids,
  uncited rules, dangling links, choice fields, rule inputs vs declared facts,
  AND independent re-computation of every scenario sum. ALL CHECKS PASS.
- Guard verified: `manage.py load_1040_sch123` refuses with CommandError while
  READY_TO_SEED=False. No DB writes this session.
- Next: Ken's review walk (packet prepared in tts-tax-app session) â†’ flip â†’
  seed â†’ export SCH_1/SCH_2/SCH_3 specs + flow assertions â†’ tts-tax-app build legs.

## 2026-06-10 PM #11 â€” D_1040_017 added to the spine spec (digital-asset question)
- Ken approved closing the digital-asset question gap (REVIEW_QUEUE item) in
  tts-tax-app's session Q&A; the spine spec already carried the fact
  (`digital_assets_answer`, choice yes/no, required) but no diagnostic.
- `load_1040_spine.py`: +D_1040_017 "Digital-asset question unanswered"
  (warning; condition `digital_assets_answer is None`). Loader re-run
  (idempotent): 1040 now 17 diagnostics; everything else unchanged
  (45 rules / 91 facts / 72 lines / 33 scenarios / 16 flow assertions).
- Deployed export verified (17 diagnostics, D_1040_017 last); semantic diff vs
  the prior canonical export showed ONLY the added diagnostic. Committed to
  tts-tax-app as `server/specs/1040_spine_spec.json`.
- New helper `run_spine_check.py` (RS root): wraps `check_spine_integrity.py`
  with django.setup() â€” the checker imports loader modules that touch models
  and can't run bare. (Note: `poetry run python -c` with a MULTILINE script
  silently produces nothing on this Windows box â€” use wrapper files.)

## 2026-06-10 PM #5b â€” 1040 SPINE seeded on Ken's approval
- Review packet walked with Ken in-session (constants per year, the Tax Table
  midpoint/half-up convention inference, diagnostics severities, stub
  retirement, 33 scenarios). **Approved as authored.**
- `READY_TO_SEED` flipped â†’ `load_1040_spine` run: stub retired (R001/R002 +
  line_11_agi + line 11), then 91 facts / 45 rules / 72 links / 72 lines /
  16 diagnostics / 33 scenarios / 16 flow assertions. RS DB: 30 forms (1040
  updated in place), FlowAssertions 51, all 1040 rules cited.
- Deployed export verified: `lookup/1040/export/` returns the spine (metadata
  correct, R-TAX-02 present, stub rules absent, TT-5 half-up pin intact).
  Committed to tts-tax-app as `server/specs/1040_spine_spec.json`.
- `/api/flow-assertions/export/?entity_type=1040` now returns 36 (13 CTC +
  7 SCH1A + 16 SPINE). The 16 spine assertions are STAGED in tts-tax-app
  (`flow_assertions_1040_spine_pending.json`) â€” wired leg by leg as compute lands.

## 2026-06-10 PM #5 â€” 1040 SPINE spec authored (Sprint Topic 1), READY_TO_SEED=False
- `specs/management/commands/load_1040_spine.py` authored: updates the Session-14
  "1040" stub TaxForm in place into the full spine spec. **45 rules (100% cited,
  72 authority links), 91 facts, 72 lines, 16 diagnostics, 33 scenarios, 16 flow
  assertions (FA-1040-SPINE-01..16), 11 new authority sources.**
- Stub retirement: the loader deletes R001/R002 (re-specified as R-CR-03/R-PAY-06),
  fact `line_11_agi` (â†’ `agi`), and line "11" (â†’ 11a/11b) with stdout notes.
- All constants transcribed from primary sources fetched + layout-extracted the
  same day: 2025 f1040.pdf (both pages, line by line); Pub 1040-TT (2025) Tax
  Table + Tax Computation Worksheet; i1040gi (2025) Line 16 routing / std-ded
  exceptions / L37-38 rules; Pub 501 (2025) Tables 6/7/8; RP 2024-40 Â§2.01;
  RP 2025-32 Â§4.01/Â§4.14; OBBBA Â§70102.
- **Tax Table convention verified, not assumed:** rows are $10/$25/$50 bands
  (0-5â†’$0; 5-25 by $10; 25-3,000 by $25; 3,000-100,000 by $50); row tax = rate
  schedule at the band MIDPOINT rounded HALF-UP (pinned by published rows
  302.50â†’303, 357.50â†’358, and the 99,950-100,000 row across all four columns).
  QSS uses the MFJ column (footnote). â‰¥$100,000 â†’ TCW â‰¡ cumulative brackets
  (verified equal at $100,000). The midpoint inference is flagged for Ken's
  explicit blessing in the review packet.
- `check_spine_integrity.py` (repo root): pre-seed content-list checker â€”
  uncited rules / dangling links / duplicate ids / excerpt+choice field
  validation. Run via `Get-Content check_spine_integrity.py -Raw | poetry run
  python manage.py shell` (or exec in a shell). All checks pass.
- Guard verified: `manage.py load_1040_spine` refuses with CommandError while
  `READY_TO_SEED = False`. No DB writes this session.
- Next: Ken's review walk (packet prepared in tts-tax-app session) â†’ flip â†’
  seed â†’ export â†’ wire into tts-tax-app compute.

## 2026-06-10 PM â€” SCH_1A seeded on Ken's approval
- Review packet walked with Ken in-session (constants, rounding directions,
  17 requires_human_review excerpts, diagnostics severities, 5 documented
  v1 deviations in tts-tax-app). **Approved.**
- `READY_TO_SEED` flipped â†’ `load_sch_1a` run: 38 rules, 47 lines, 31 facts,
  6 diagnostics, 21 scenarios, 7 flow assertions, 66 authority links (all
  rules cited). RS DB now 30 forms.
- Export verified via `lookup/SCH_1A/export/`; committed to tts-tax-app as
  the canonical `server/specs/sch_1a_spec.json`. tts-tax-app implemented
  Part IV (car loan) from it the same day â€” all 21 scenarios green.
- Flow-assertion export note: `/api/flow-assertions/export/?entity_type=1040`
  returns 20 (13 CTC + 7 SCH1A). RS SCH1A-01..04 duplicate locally-wired
  assertions in tts-tax-app; -05/-06/-07 were newly wired there.

## 2026-06-10 â€” 1040 campaign Phase 0 state audit (read-only)
- No RS code or data changes. Inventoried authored specs vs. the deployed DB.
- Deployed RS DB holds 29 seeded forms (all status=draft). 1040-relevant: SCH_8812
  (1,140 facts/rules â€” exported + implemented in tts-tax-app), 1040 stub (2 rules:
  L11/19/28), plus business forms reusable at the 1040 level.
- **SCH_1A status confirmed: authored, NOT seeded.** All six parts + 21 test
  scenarios + 7 diagnostics + 8 flow assertions live in
  `specs/management/commands/load_sch_1a.py` with `READY_TO_SEED = False` (line 77).
  Awaiting Ken's review â†’ flip â†’ seed â†’ export â†’ verify (tts-tax-app already
  implements Parts I/II/III/V/VI from Ken's scope docs; Part IV is spec-ahead-of-compute).
- Noted: RS has no per-form `ready_to_seed` DB field â€” the sentinel is per-loader-command.
- RS root STATUS.md / MEMORY.md / DECISIONS.md are stale (last touched 2026-04-27,
  pre-dating Sessions 14-17). Update them next time RS work happens.

## Backfill â€” sessions before this log existed (from git history)
- **2026-06-03 (Sessions 16-17):** `load_sch_1a.py` authored â€” scaffold, all six parts,
  21 scenarios (`4273295`, `0d49a44`, `ab45137`). NOT seeded.
- **2026-05-26 (Session 14):** SCH_8812 (CTC/ACTC) spec authored + seeded + exported
  (`98c2fb2`, `61da16a`); exports in `exports/session14/`.
- **2026-03 (Sessions 6-13):** 1120-S family complete â€” 29 forms, flow-assertion
  model + API + export endpoint, lookup-by-form-number API.
