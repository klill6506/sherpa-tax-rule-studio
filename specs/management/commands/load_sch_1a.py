"""Load Schedule 1-A (SCH_1A) spec — STRUCTURE-ONLY SCAFFOLD.

Session 15 (2026-06-03): Schedule 1-A is a TY 2025 form expected by tts-tax-app.
A prior session-15 diagnostic confirmed no Rule Studio records exist for SCH_1A —
only a flat cache file in tts-tax-app/server/specs/ that self-declares as non-RS.

This file is the FRAME Ken will populate. It mirrors `load_1040_ctc.py`'s
structure exactly: same record types, same helper methods, same idempotent
update_or_create pattern. Every content slot is an EMPTY, clearly-labeled TODO
list. There is no tax content of any kind in this file — no rules, amounts,
caps, phaseouts, rates, dates, or IRS citations. Ken authors all of that.

Safety guard
------------
The command REFUSES to seed while content is unauthored. Two gates:

  1. `READY_TO_SEED = False` (top-of-file sentinel). Ken flips to True ONLY
     after authoring is complete and reviewed.
  2. Essential content lists (sources, rules, lines) must each have ≥ 1 entry.

If either gate fails, `handle()` raises CommandError BEFORE any DB operation.
This prevents a hollow SCH_1A form from being registered — an empty spec that
resolves would falsely satisfy tts-tax-app's spec-first gate.

To populate
-----------
1. Fill in TODO sections in the module-level data lists below.
2. Verify against IRS authority (statute / form / instructions / pub).
3. Run the command in --dry-run mode (TODO: add flag if useful) or with
   READY_TO_SEED still False to see the diagnostic checklist of what's missing.
4. Once authoring is complete: set READY_TO_SEED = True.
5. Run: `poetry run python manage.py load_sch_1a`.

Idempotent via update_or_create — safe to re-run after edits.

DO NOT relax the safety guard to silence the error. The guard exists because an
empty spec is worse than a missing spec: it falsely satisfies downstream checks.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sources.models import (
    AuthorityExcerpt,
    AuthorityFormLink,
    AuthoritySource,
    AuthoritySourceTopic,
    AuthorityTopic,
    RuleAuthorityLink,
)
from specs.models import (
    FlowAssertion,
    FormDiagnostic,
    FormFact,
    FormLine,
    FormRule,
    TaxForm,
    TestScenario,
)


# ═══════════════════════════════════════════════════════════════════════════
# SAFETY GUARD — Ken: flip to True ONLY after authoring is complete.
# ═══════════════════════════════════════════════════════════════════════════

READY_TO_SEED = False


# ═══════════════════════════════════════════════════════════════════════════
# FORM IDENTITY
# Form-number and entity-type are structural identifiers, not tax content.
# Title is a placeholder for Ken to confirm verbatim against the IRS-issued form.
# ═══════════════════════════════════════════════════════════════════════════

FORM_NUMBER = "SCH_1A"
FORM_TITLE = "[TODO: Ken — verbatim form title from IRS-issued Schedule 1-A header]"
FORM_JURISDICTION = "FED"
FORM_ENTITY_TYPES = ["1040"]
FORM_TAX_YEAR = 2025
FORM_VERSION = 1
FORM_STATUS = "draft"
FORM_NOTES = "[TODO: Ken — short summary of what this spec covers and any deferred parts.]"

# Existing source codes to look up (not modify). Add codes here when Ken needs
# to attach links to authorities already in the DB.
EXISTING_SOURCES_TO_REFERENCE: list[str] = [
    # TODO: Ken — e.g. "IRS_2025_1040_INSTR" if SCH_1A excerpts attach there.
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY TOPICS
# ═══════════════════════════════════════════════════════════════════════════
# Pairs of (topic_code, topic_name). Idempotent via update_or_create.

AUTHORITY_TOPICS: list[tuple[str, str]] = [
    # TODO: Ken — add topic_code / topic_name pairs as needed.
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY SOURCES (with embedded excerpts)
# Each entry: full source record dict + nested `excerpts` list + `topics` list.
# See load_1040_ctc.py for the field shape and FRESH_SOURCES examples.
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_SOURCES: list[dict] = [
    # TODO: Ken — author each authority record:
    #   {
    #     "source_code": ...,
    #     "source_type": ...,        # code_section | official_form | official_instruction | official_publication | ...
    #     "source_rank": ...,        # controlling | primary_official | implementation_official | ...
    #     "jurisdiction_code": "FED",
    #     "title": ...,
    #     "citation": ...,
    #     "issuer": ...,             # Congress | IRS | Treasury | ...
    #     "official_url": ...,
    #     "current_status": "active",
    #     "is_substantive_authority": True/False,
    #     "trust_score": 0.0-10.0,
    #     "requires_human_review": True/False,
    #     "notes": ...,
    #     "topics": [topic_codes...],
    #     "excerpts": [
    #         {
    #             "excerpt_label": ...,
    #             "location_reference": ...,
    #             "excerpt_text": ...,     # verbatim quote
    #             "summary_text": ...,     # short paraphrase
    #             "is_key_excerpt": True/False,
    #         },
    #         ...
    #     ],
    #   },
]

# Excerpts to ADD to an EXISTING source (rather than create a new one).
# Each entry: (existing_source_code, excerpt_dict).
NEW_EXCERPTS_ON_EXISTING: list[tuple[str, dict]] = [
    # TODO: Ken — e.g. ("IRS_2025_1040_INSTR", {"excerpt_label": ..., "excerpt_text": ..., ...})
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM FACTS
# Inputs the form needs. Per-row facts use a clear prefix; return-level facts
# have no prefix. Document iteration semantics in the `notes` field.
# ═══════════════════════════════════════════════════════════════════════════

FORM_FACTS: list[dict] = [
    # ── Part I — MAGI ──
    # TODO: Ken

    # ── Part II — Tips ──
    # TODO: Ken

    # ── Part III — Overtime ──
    # TODO: Ken

    # ── Part IV — Car Loan Interest ──
    # TODO: Ken

    # ── Part V — Senior Deduction ──
    # TODO: Ken

    # ── Part VI — Total ──
    # TODO: Ken
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM RULES
# Each rule's `description` MUST document iteration semantics
# (ONCE PER RETURN / ONCE PER ROW / AGGREGATE).
# ═══════════════════════════════════════════════════════════════════════════

FORM_RULES: list[dict] = [
    # ── Part I — MAGI ──
    # TODO: Ken

    # ── Part II — Tips ──
    # TODO: Ken

    # ── Part III — Overtime ──
    # TODO: Ken

    # ── Part IV — Car Loan Interest ──
    # TODO: Ken

    # ── Part V — Senior Deduction ──
    # TODO: Ken

    # ── Part VI — Total ──
    # TODO: Ken
]


# ═══════════════════════════════════════════════════════════════════════════
# RULE → AUTHORITY LINKS
# Tuples of (rule_id, source_code, support_level, relevance_note).
# Every rule MUST have at least one link. Session 14 hit 100% coverage.
# ═══════════════════════════════════════════════════════════════════════════

RULE_AUTHORITY_LINKS: list[tuple[str, str, str, str]] = [
    # ── Part I — MAGI ──
    # TODO: Ken

    # ── Part II — Tips ──
    # TODO: Ken

    # ── Part III — Overtime ──
    # TODO: Ken

    # ── Part IV — Car Loan Interest ──
    # TODO: Ken

    # ── Part V — Senior Deduction ──
    # TODO: Ken

    # ── Part VI — Total ──
    # TODO: Ken
]


# ═══════════════════════════════════════════════════════════════════════════
# FORM LINES (line_map)
# ═══════════════════════════════════════════════════════════════════════════

FORM_LINES: list[dict] = [
    # ── Part I — MAGI ──
    # TODO: Ken

    # ── Part II — Tips ──
    # TODO: Ken

    # ── Part III — Overtime ──
    # TODO: Ken

    # ── Part IV — Car Loan Interest ──
    # TODO: Ken

    # ── Part V — Senior Deduction ──
    # TODO: Ken

    # ── Part VI — Total ──
    # TODO: Ken
]


# ═══════════════════════════════════════════════════════════════════════════
# DIAGNOSTICS
# severity ∈ {error, warning, info}.
# ═══════════════════════════════════════════════════════════════════════════

FORM_DIAGNOSTICS: list[dict] = [
    # ── Part I — MAGI ──
    # TODO: Ken

    # ── Part II — Tips ──
    # TODO: Ken

    # ── Part III — Overtime ──
    # TODO: Ken

    # ── Part IV — Car Loan Interest ──
    # TODO: Ken

    # ── Part V — Senior Deduction ──
    # TODO: Ken

    # ── Part VI — Total ──
    # TODO: Ken
]


# ═══════════════════════════════════════════════════════════════════════════
# TEST SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════

TEST_SCENARIOS: list[dict] = [
    # ── Part I — MAGI ──
    # TODO: Ken

    # ── Part II — Tips ──
    # TODO: Ken

    # ── Part III — Overtime ──
    # TODO: Ken

    # ── Part IV — Car Loan Interest ──
    # TODO: Ken

    # ── Part V — Senior Deduction ──
    # TODO: Ken

    # ── Part VI — Total ──
    # TODO: Ken
]


# ═══════════════════════════════════════════════════════════════════════════
# FLOW ASSERTIONS
# ID convention (Session 14 standard): FA-1040-<TOPIC>-NN, TI-1040-<TOPIC>-X.
# ═══════════════════════════════════════════════════════════════════════════

FLOW_ASSERTIONS: list[dict] = [
    # ── Part I — MAGI ──
    # TODO: Ken

    # ── Part II — Tips ──
    # TODO: Ken

    # ── Part III — Overtime ──
    # TODO: Ken

    # ── Part IV — Car Loan Interest ──
    # TODO: Ken

    # ── Part V — Senior Deduction ──
    # TODO: Ken

    # ── Part VI — Total ──
    # TODO: Ken
]


# ═══════════════════════════════════════════════════════════════════════════
# AUTHORITY FORM LINKS
# Tuples of (source_code, link_type). e.g. (source, "governs") | "informs".
# ═══════════════════════════════════════════════════════════════════════════

AUTHORITY_FORM_LINKS: list[tuple[str, str]] = [
    # TODO: Ken
]


# ═══════════════════════════════════════════════════════════════════════════
# Command
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = (
        "Load Schedule 1-A (SCH_1A) spec into Rule Studio. "
        "SCAFFOLD: refuses to seed until Ken authors content + sets READY_TO_SEED=True."
    )

    # The minimum-content gate. The form is structurally hollow without at least
    # one entry in each of these. Adjust this list if/when authoring intentionally
    # leaves a category empty (e.g. no diagnostics for a given form).
    REQUIRED_CONTENT_LISTS: tuple[tuple[str, list], ...] = (
        ("AUTHORITY_SOURCES",     AUTHORITY_SOURCES),
        ("FORM_RULES",            FORM_RULES),
        ("FORM_LINES",            FORM_LINES),
        ("RULE_AUTHORITY_LINKS",  RULE_AUTHORITY_LINKS),
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        # ─── SAFETY GUARD — runs BEFORE any DB operation ────────────────────
        self._guard_against_hollow_seed()
        # ─── End guard ──────────────────────────────────────────────────────

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\nLoad {FORM_NUMBER} spec\n"
        ))

        self._load_topics()
        sources = self._load_sources()
        self._load_new_excerpts_on_existing(sources)
        form = self._upsert_form()
        self._upsert_facts(form)
        rules = self._upsert_rules(form)
        self._upsert_authority_links(rules, sources)
        self._upsert_lines(form)
        self._upsert_diagnostics(form)
        self._upsert_tests(form)
        self._upsert_form_links(sources)
        self._load_flow_assertions()
        self._report_totals()

    # ─────────────────────────────────────────────────────────────────────────
    # Safety guard
    # ─────────────────────────────────────────────────────────────────────────

    def _guard_against_hollow_seed(self):
        """Refuse to write anything until Ken has authored content AND flipped READY_TO_SEED."""
        empty = [name for name, lst in self.REQUIRED_CONTENT_LISTS if not lst]

        # Title check — placeholder strings must be replaced.
        title_is_placeholder = "[TODO" in FORM_TITLE
        if title_is_placeholder:
            empty.append("FORM_TITLE (still a [TODO] placeholder)")

        if not READY_TO_SEED or empty:
            checklist = "\n  ".join(f"- {name}" for name, lst in self.REQUIRED_CONTENT_LISTS) or "(none required)"
            still_empty = "\n  ".join(f"- {n}" for n in empty) or "(all populated)"
            raise CommandError(
                "\n"
                f"REFUSING TO SEED {FORM_NUMBER}: scaffold has not been authored.\n"
                "\n"
                "This command is a STRUCTURE-ONLY scaffold (Session 15). It will not\n"
                "register a hollow form record because an empty spec falsely satisfies\n"
                "tts-tax-app's spec-first gate ('stop if no spec').\n"
                "\n"
                f"READY_TO_SEED = {READY_TO_SEED} (must be True to proceed)\n"
                "\n"
                "Content checklist:\n"
                f"  {checklist}\n"
                "\n"
                "Currently empty / placeholder:\n"
                f"  {still_empty}\n"
                "\n"
                "To proceed: author content in the module-level data lists at the top\n"
                "of this file, then set READY_TO_SEED = True. Idempotent via\n"
                "update_or_create — safe to re-run after edits."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Topics
    # ─────────────────────────────────────────────────────────────────────────

    def _load_topics(self):
        ct = 0
        for code, name in AUTHORITY_TOPICS:
            _, created = AuthorityTopic.objects.update_or_create(
                topic_code=code, defaults={"topic_name": name},
            )
            if created:
                ct += 1
        self.stdout.write(f"Topics: {ct} new ({len(AUTHORITY_TOPICS)} total in batch)")

    # ─────────────────────────────────────────────────────────────────────────
    # Sources
    # ─────────────────────────────────────────────────────────────────────────

    def _load_sources(self) -> dict[str, AuthoritySource]:
        sources: dict[str, AuthoritySource] = {}
        for src_data in AUTHORITY_SOURCES:
            src_data = dict(src_data)
            excerpts_data = src_data.pop("excerpts", [])
            topic_codes = src_data.pop("topics", [])
            source, _ = AuthoritySource.objects.update_or_create(
                source_code=src_data["source_code"], defaults=src_data,
            )
            sources[source.source_code] = source
            for exc in excerpts_data:
                exc = dict(exc)
                AuthorityExcerpt.objects.update_or_create(
                    authority_source=source, excerpt_label=exc["excerpt_label"], defaults=exc,
                )
            for tc in topic_codes:
                topic = AuthorityTopic.objects.filter(topic_code=tc).first()
                if topic:
                    AuthoritySourceTopic.objects.get_or_create(
                        authority_source=source, authority_topic=topic,
                    )
        for code in EXISTING_SOURCES_TO_REFERENCE:
            src = AuthoritySource.objects.filter(source_code=code).first()
            if src:
                sources[code] = src
        self.stdout.write(f"Sources ready: {len(sources)}")
        return sources

    def _load_new_excerpts_on_existing(self, sources):
        ct = 0
        for code, exc in NEW_EXCERPTS_ON_EXISTING:
            src = sources.get(code) or AuthoritySource.objects.filter(source_code=code).first()
            if not src:
                self.stdout.write(self.style.WARNING(
                    f"  source {code} not found — skipping new excerpt"
                ))
                continue
            exc = dict(exc)
            AuthorityExcerpt.objects.update_or_create(
                authority_source=src, excerpt_label=exc["excerpt_label"], defaults=exc,
            )
            ct += 1
        if ct:
            self.stdout.write(f"  {ct} new excerpts on existing sources")

    # ─────────────────────────────────────────────────────────────────────────
    # Form helpers (mirror load_1040_ctc.py exactly)
    # ─────────────────────────────────────────────────────────────────────────

    def _upsert_form(self) -> TaxForm:
        form, created = TaxForm.objects.update_or_create(
            form_number=FORM_NUMBER,
            jurisdiction=FORM_JURISDICTION,
            tax_year=FORM_TAX_YEAR,
            version=FORM_VERSION,
            defaults={
                "form_title": FORM_TITLE,
                "entity_types": FORM_ENTITY_TYPES,
                "status": FORM_STATUS,
                "notes": FORM_NOTES,
            },
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} {FORM_NUMBER}")
        return form

    def _upsert_facts(self, form):
        for f in FORM_FACTS:
            f = dict(f)
            FormFact.objects.update_or_create(
                tax_form=form, fact_key=f.pop("fact_key"), defaults=f,
            )
        self.stdout.write(f"  {len(FORM_FACTS)} facts")

    def _upsert_rules(self, form) -> dict[str, FormRule]:
        created = {}
        for r in FORM_RULES:
            r = dict(r)
            rule, _ = FormRule.objects.update_or_create(
                tax_form=form, rule_id=r.pop("rule_id"), defaults=r,
            )
            created[rule.rule_id] = rule
        self.stdout.write(f"  {len(created)} rules")
        return created

    def _upsert_authority_links(self, rules, sources):
        ct = 0
        for rule_id, source_code, level, note in RULE_AUTHORITY_LINKS:
            rule, source = rules.get(rule_id), sources.get(source_code)
            if rule and source:
                RuleAuthorityLink.objects.get_or_create(
                    form_rule=rule, authority_source=source,
                    defaults={"support_level": level, "relevance_note": note},
                )
                ct += 1
        self.stdout.write(f"  {ct} authority links")

    def _upsert_lines(self, form):
        for ln in FORM_LINES:
            ln = dict(ln)
            FormLine.objects.update_or_create(
                tax_form=form, line_number=ln.pop("line_number"), defaults=ln,
            )
        self.stdout.write(f"  {len(FORM_LINES)} lines")

    def _upsert_diagnostics(self, form):
        for d in FORM_DIAGNOSTICS:
            d = dict(d)
            FormDiagnostic.objects.update_or_create(
                tax_form=form, diagnostic_id=d.pop("diagnostic_id"), defaults=d,
            )
        self.stdout.write(f"  {len(FORM_DIAGNOSTICS)} diagnostics")

    def _upsert_tests(self, form):
        for t in TEST_SCENARIOS:
            t = dict(t)
            TestScenario.objects.update_or_create(
                tax_form=form, scenario_name=t.pop("scenario_name"), defaults=t,
            )
        self.stdout.write(f"  {len(TEST_SCENARIOS)} test scenarios")

    def _upsert_form_links(self, sources):
        for source_code, link_type in AUTHORITY_FORM_LINKS:
            source = sources.get(source_code) or AuthoritySource.objects.filter(
                source_code=source_code,
            ).first()
            if source:
                AuthorityFormLink.objects.get_or_create(
                    authority_source=source, form_code=FORM_NUMBER, link_type=link_type,
                    defaults={"note": f"{source_code} -> {FORM_NUMBER}"},
                )

    # ─────────────────────────────────────────────────────────────────────────
    # Flow assertions
    # ─────────────────────────────────────────────────────────────────────────

    def _load_flow_assertions(self):
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(
                assertion_id=a.pop("assertion_id"), defaults=a,
            )
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")

    # ─────────────────────────────────────────────────────────────────────────
    # Report
    # ─────────────────────────────────────────────────────────────────────────

    def _report_totals(self):
        def _safe(text):
            return text.encode("ascii", errors="replace").decode("ascii")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"DATABASE TOTALS (after load_{FORM_NUMBER.lower()})")
        self.stdout.write("=" * 60)
        self.stdout.write(f"TaxForms:           {TaxForm.objects.count()}")
        self.stdout.write(f"FormFacts:          {FormFact.objects.count()}")
        self.stdout.write(f"FormRules:          {FormRule.objects.count()}")
        self.stdout.write(f"FormLines:          {FormLine.objects.count()}")
        self.stdout.write(f"FormDiagnostics:    {FormDiagnostic.objects.count()}")
        self.stdout.write(f"TestScenarios:      {TestScenario.objects.count()}")
        self.stdout.write(f"AuthoritySources:   {AuthoritySource.objects.count()}")
        self.stdout.write(f"AuthorityExcerpts:  {AuthorityExcerpt.objects.count()}")
        self.stdout.write(f"RuleAuthorityLinks: {RuleAuthorityLink.objects.count()}")
        self.stdout.write(f"AuthorityFormLinks: {AuthorityFormLink.objects.count()}")
        self.stdout.write(f"FlowAssertions:     {FlowAssertion.objects.count()}")

        all_rules = FormRule.objects.filter(tax_form__form_number=FORM_NUMBER)
        uncited = [r for r in all_rules if not r.authority_links.exists()]
        if uncited:
            self.stdout.write(self.style.WARNING(
                f"\n{FORM_NUMBER} rules with ZERO authority links: {len(uncited)}"
            ))
            for r in uncited[:20]:
                self.stdout.write(_safe(f"  {r.rule_id}: {r.title}"))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nAll {FORM_NUMBER} rules have authority links."
            ))

        self.stdout.write("=" * 60)
