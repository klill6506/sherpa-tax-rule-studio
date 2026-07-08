"""change_register — the RS tax-law-change funnel (manual-clip lifecycle).

The front-of-the-front-door: a law change is recorded here, triaged, then PROMOTED into a
WORK_ORDERS INTAKE order — where the existing front door (gap-check -> research -> Gate-1 ->
author -> seed -> tts build) takes over. Promotion NEVER crosses a gate unattended.

Lifecycle: DETECTED -> TRIAGED -> PROMOTED (or DISMISSED).

Usage:
  # 1) record a change (DETECTED)
  manage.py change_register add --title "Rev. Proc. 2026-XX supersedes 2025-23 (auto-change list)" \
      --summary "New annual automatic-change list; DCN table refreshed." \
      --forms 3115 --jurisdiction US --tax-year 2026 --source REVPROC_2025_23

  # 2) triage it (TRIAGED) — record the assessment
  manage.py change_register triage --code CR-2026-001 --substantive \
      --forms 3115,4562 --notes "DCN 7 unchanged; re-verify the revision + list cite."

  # 3) promote it to a WORK_ORDERS order (PROMOTED)
  manage.py change_register promote --code CR-2026-001 --work-order WO-24

  # or dismiss a non-substantive item
  manage.py change_register dismiss --code CR-2026-002 --notes "Editorial only; no rule impact."

  # list (optionally by status)
  manage.py change_register list [--status detected]
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from sources.models import (
    AuthoritySource, ChangeDetectionSource, ChangeRegisterItem, ChangeStatus,
)


def _next_change_code(year: int) -> str:
    """CR-<year>-<zero-padded seq>, sequential within the year."""
    prefix = f"CR-{year}-"
    existing = ChangeRegisterItem.objects.filter(change_code__startswith=prefix).values_list("change_code", flat=True)
    seqs = []
    for c in existing:
        tail = c.rsplit("-", 1)[-1]
        if tail.isdigit():
            seqs.append(int(tail))
    return f"{prefix}{(max(seqs) + 1) if seqs else 1:03d}"


def _csv(val):
    return [v.strip() for v in val.split(",") if v.strip()] if val else []


class Command(BaseCommand):
    help = "Record / triage / promote / dismiss / list tax-law changes (the RS change-register funnel)."

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["add", "triage", "promote", "dismiss", "list"])
        parser.add_argument("--code", help="Change code (CR-YYYY-NNN) for triage/promote/dismiss.")
        parser.add_argument("--title")
        parser.add_argument("--summary")
        parser.add_argument("--forms", help="Comma-separated affected form numbers, e.g. 3115,4562")
        parser.add_argument("--rules", help="Comma-separated affected rule_ids (optional).")
        parser.add_argument("--jurisdiction", default="US")
        parser.add_argument("--tax-year", type=int)
        parser.add_argument("--source", help="AuthoritySource.source_code that moved (optional).")
        parser.add_argument("--detected-via", choices=[c[0] for c in ChangeDetectionSource.choices],
                            default=ChangeDetectionSource.MANUAL_CLIP)
        parser.add_argument("--work-order", help="WORK_ORDERS order id for promote, e.g. WO-24.")
        parser.add_argument("--notes", help="Triage / dismissal notes.")
        parser.add_argument("--substantive", dest="substantive", action="store_true", help="Triage: requires authoring.")
        parser.add_argument("--not-substantive", dest="substantive", action="store_false", help="Triage: no authoring needed.")
        parser.set_defaults(substantive=None)
        parser.add_argument("--status", help="list filter: detected/triaged/promoted/dismissed.")

    def handle(self, *args, **o):
        getattr(self, f"_{o['action']}")(o)

    # ── add (DETECTED) ────────────────────────────────────────────────────
    @transaction.atomic
    def _add(self, o):
        if not o.get("title") or not o.get("summary"):
            raise CommandError("add requires --title and --summary.")
        src = None
        if o.get("source"):
            src = AuthoritySource.objects.filter(source_code=o["source"]).first()
            if not src:
                raise CommandError(f"AuthoritySource '{o['source']}' not found (seed it first, or omit --source).")
        code = _next_change_code(timezone.now().year)
        item = ChangeRegisterItem.objects.create(
            change_code=code, title=o["title"], summary=o["summary"],
            jurisdiction_code=o["jurisdiction"], tax_year=o.get("tax_year"),
            detected_via=o["detected_via"], status=ChangeStatus.DETECTED,
            authority_source=src, affected_forms=_csv(o.get("forms")),
        )
        self.stdout.write(self.style.SUCCESS(f"DETECTED {item.change_code}: {item.title}"))
        if item.affected_forms:
            self.stdout.write(f"  affected forms: {', '.join(item.affected_forms)}")
        self.stdout.write("  next: triage it -> manage.py change_register triage --code " + code)

    # ── triage (TRIAGED) ──────────────────────────────────────────────────
    @transaction.atomic
    def _triage(self, o):
        item = self._get(o)
        if o.get("substantive") is not None:
            item.is_substantive = o["substantive"]
        if o.get("forms"):
            item.affected_forms = _csv(o["forms"])
        if o.get("rules"):
            item.affected_rule_ids = _csv(o["rules"])
        if o.get("notes"):
            item.triage_notes = o["notes"]
        item.status = ChangeStatus.TRIAGED
        item.save()
        verdict = "SUBSTANTIVE" if item.is_substantive else ("non-substantive" if item.is_substantive is False else "unassessed")
        self.stdout.write(self.style.SUCCESS(f"TRIAGED {item.change_code} ({verdict})"))
        self.stdout.write(f"  forms: {', '.join(item.affected_forms) or '(none)'}")
        if item.is_substantive:
            self.stdout.write("  next: promote -> manage.py change_register promote --code "
                              f"{item.change_code} --work-order WO-NN")
        else:
            self.stdout.write("  next: dismiss -> manage.py change_register dismiss --code " + item.change_code)

    # ── promote (PROMOTED -> WORK_ORDERS INTAKE) ──────────────────────────
    @transaction.atomic
    def _promote(self, o):
        item = self._get(o)
        if not o.get("work_order"):
            raise CommandError("promote requires --work-order (e.g. WO-24).")
        if item.is_substantive is False:
            raise CommandError(f"{item.change_code} was triaged non-substantive; dismiss it instead of promoting.")
        item.promoted_work_order = o["work_order"]
        item.promoted_at = timezone.now()
        item.status = ChangeStatus.PROMOTED
        item.save()
        self.stdout.write(self.style.SUCCESS(f"PROMOTED {item.change_code} -> {item.promoted_work_order}"))
        self.stdout.write("  Now open that order in WORK_ORDERS.md INTAKE and run the front door:")
        self.stdout.write(f"  gap-check ({', '.join(item.affected_forms) or 'affected forms'}) -> research-verify -> "
                          "Gate-1 scope walk -> author -> seed. NOTHING crosses a gate unattended.")

    # ── dismiss (DISMISSED) ───────────────────────────────────────────────
    @transaction.atomic
    def _dismiss(self, o):
        item = self._get(o)
        if o.get("notes"):
            item.triage_notes = o["notes"]
        item.is_substantive = False
        item.status = ChangeStatus.DISMISSED
        item.save()
        self.stdout.write(self.style.WARNING(f"DISMISSED {item.change_code}: {item.triage_notes or '(no reason given)'}"))

    # ── list ──────────────────────────────────────────────────────────────
    def _list(self, o):
        qs = ChangeRegisterItem.objects.all()
        if o.get("status"):
            qs = qs.filter(status=o["status"])
        n = qs.count()
        self.stdout.write(self.style.MIGRATE_HEADING(f"\nChange register — {n} item(s)\n"))
        for it in qs:
            wo = f" -> {it.promoted_work_order}" if it.promoted_work_order else ""
            forms = f" [{', '.join(it.affected_forms)}]" if it.affected_forms else ""
            ty = f" TY{it.tax_year}" if it.tax_year else ""
            self.stdout.write(f"  {it.change_code}  {it.status.upper():9}{ty}{forms}{wo}")
            self.stdout.write(f"      {it.title}")
        if not n:
            self.stdout.write("  (empty — record one with: manage.py change_register add --title ... --summary ...)")

    def _get(self, o) -> ChangeRegisterItem:
        if not o.get("code"):
            raise CommandError("This action requires --code (CR-YYYY-NNN).")
        item = ChangeRegisterItem.objects.filter(change_code=o["code"]).first()
        if not item:
            raise CommandError(f"No change-register item '{o['code']}'.")
        return item
