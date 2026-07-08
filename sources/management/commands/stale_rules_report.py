"""stale_rules_report — the blast-radius report for a tax-law change (Authoritative-Source Rule step 5).

When a source moves, which authored rules depend on it? This READ-ONLY report answers that so Ken knows
what to re-verify. It does NOT touch any rule (Ken's D-26 scoping: "report, don't auto-edit") — it only
reads RuleAuthorityLink / affected_forms and prints the candidates.

Three reasons a rule shows up, strongest first:
  cites_source     — the rule has a RuleAuthorityLink to the moved AuthoritySource (it literally cites it)
  named            — the rule_id is listed in the change item's affected_rule_ids (triage pinned it)
  on_affected_form — the rule lives on a form listed in the change item's affected_forms (form-level sweep)

Input (one of):
  --change CR-YYYY-NNN   use that change item's authority_source + affected_rule_ids + affected_forms
  --source SOURCE_CODE   trace one AuthoritySource directly (cites_source only)

Usage:
  manage.py stale_rules_report --change CR-2026-001
  manage.py stale_rules_report --source REVPROC_2025_23
  manage.py stale_rules_report --change CR-2026-001 --json
"""
import json

from django.core.management.base import BaseCommand, CommandError

from sources.models import AuthoritySource, ChangeRegisterItem, RuleAuthorityLink
from specs.models import FormRule

REASON_RANK = {"cites_source": 0, "named": 1, "on_affected_form": 2}


class Command(BaseCommand):
    help = "Report the authored rules a tax-law change may make stale (read-only blast radius)."

    def add_arguments(self, parser):
        parser.add_argument("--change", help="Change code CR-YYYY-NNN.")
        parser.add_argument("--source", help="AuthoritySource.source_code to trace directly.")
        parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")

    def handle(self, *args, **o):
        if not o.get("change") and not o.get("source"):
            raise CommandError("Provide --change CR-YYYY-NNN or --source SOURCE_CODE.")

        sources, affected_forms, affected_rule_ids, label = [], [], [], ""
        if o.get("change"):
            item = ChangeRegisterItem.objects.filter(change_code=o["change"]).first()
            if not item:
                raise CommandError(f"No change-register item '{o['change']}'.")
            if item.authority_source_id:
                sources = [item.authority_source]
            affected_forms = item.affected_forms or []
            affected_rule_ids = item.affected_rule_ids or []
            label = (f"{item.change_code} (source {item.authority_source.source_code if item.authority_source else '—'}"
                     f"; forms {', '.join(affected_forms) or '—'})")
        if o.get("source"):
            src = AuthoritySource.objects.filter(source_code=o["source"]).first()
            if not src:
                raise CommandError(f"No AuthoritySource '{o['source']}'.")
            sources = [src]
            label = label or f"source {src.source_code}"

        # rule_pk -> {rule, reason, support_level, relevance_note}
        found: dict = {}

        def _add(rule, reason, support_level=None, note=None):
            cur = found.get(rule.pk)
            if cur and REASON_RANK[cur["reason"]] <= REASON_RANK[reason]:
                return  # keep the stronger reason already recorded
            found[rule.pk] = {"rule": rule, "reason": reason, "support_level": support_level, "relevance_note": note}

        # 1) cites_source — rules with a RuleAuthorityLink to any moved source
        if sources:
            for link in (RuleAuthorityLink.objects
                         .filter(authority_source__in=sources)
                         .select_related("form_rule", "form_rule__tax_form", "authority_source")):
                _add(link.form_rule, "cites_source", link.support_level, link.relevance_note)

        # 2) named — rule_ids the triage pinned
        if affected_rule_ids:
            for rule in FormRule.objects.filter(rule_id__in=affected_rule_ids).select_related("tax_form"):
                _add(rule, "named")

        # 3) on_affected_form — every rule on an affected form
        if affected_forms:
            for rule in FormRule.objects.filter(tax_form__form_number__in=affected_forms).select_related("tax_form"):
                _add(rule, "on_affected_form")

        rows = sorted(
            found.values(),
            key=lambda r: (r["rule"].tax_form.form_number, REASON_RANK[r["reason"]], r["rule"].rule_id))

        if o.get("json"):
            self.stdout.write(json.dumps({
                "target": label,
                "rule_count": len(rows),
                "form_count": len({r["rule"].tax_form.form_number for r in rows}),
                "rules": [{
                    "form_number": r["rule"].tax_form.form_number,
                    "rule_id": r["rule"].rule_id, "title": r["rule"].title, "reason": r["reason"],
                    "support_level": r["support_level"], "relevance_note": r["relevance_note"],
                } for r in rows],
            }, indent=2))
            return

        self.stdout.write(self.style.MIGRATE_HEADING(f"\nStaleness report — {label}\n"))
        if not rows:
            self.stdout.write("  No dependent rules found. Nothing to re-verify from linkage — but confirm the change "
                              "doesn't imply a NEW rule (a gap the register can't see).")
            return

        cur_form = None
        for r in rows:
            rule, tf = r["rule"], r["rule"].tax_form
            if tf.form_number != cur_form:
                cur_form = tf.form_number
                self.stdout.write(f"\n{tf.jurisdiction} {tf.form_number} ({tf.tax_year})")
            reason = {"cites_source": "CITES SOURCE", "named": "named in triage", "on_affected_form": "on affected form"}[r["reason"]]
            extra = f" [{r['support_level']}]" if r["support_level"] else ""
            note = f' — {r["relevance_note"]}' if r["relevance_note"] else ""
            self.stdout.write(f"  {rule.rule_id:16} {reason}{extra}{note}")
            self.stdout.write(f"       {rule.title}")

        cites = sum(1 for r in rows if r["reason"] == "cites_source")
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"{len(rows)} rule(s) across {len({r['rule'].tax_form.form_number for r in rows})} form(s) "
                          f"to re-verify — {cites} cite the moved source directly.")
        self.stdout.write("Re-verify each against the updated authority (Authoritative-Source Rule step 5); "
                          "author a new WORK_ORDER if the change alters the rule.")
        self.stdout.write("=" * 60)
