"""Apply the source-controlled approval manifest (specs/approved_specs.py) to the DB.

Flips TaxForm.status draft/review -> approved for every form listed in APPROVED_FORMS.
Reproducible + idempotent: re-running is a no-op for already-approved forms. `seed_all`
runs this as its final phase so a from-scratch rebuild restores approvals from source.

Reports three drift conditions:
  - manifest entries that match no form in the DB (typo / not seeded yet)
  - forms approved in the DB that are NOT in the manifest (approval that would be lost on
    rebuild — the "lives only in Supabase" anti-pattern)

Usage:
  poetry run python manage.py approve_specs            # apply
  poetry run python manage.py approve_specs --dry-run  # report only, no writes
"""
from django.core.management.base import BaseCommand

from specs.approved_specs import APPROVED_FORMS
from specs.models import TaxForm


class Command(BaseCommand):
    help = "Set status=approved for the forms in specs/approved_specs.py (source-controlled)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report only; make no changes.")

    def handle(self, *_args, **opts):
        dry = opts["dry_run"]
        manifest_keys = set()
        flipped, already, missing = [], [], []

        for entry in APPROVED_FORMS:
            fn = entry["form_number"]
            qs = TaxForm.objects.filter(form_number__iexact=fn)
            if "jurisdiction" in entry:
                qs = qs.filter(jurisdiction=entry["jurisdiction"])
            forms = list(qs)
            if not forms:
                missing.append(fn)
                continue
            for form in forms:
                manifest_keys.add(form.form_number)
                if form.status == TaxForm.Status.APPROVED:
                    already.append(form.form_number)
                else:
                    flipped.append((form.form_number, form.status))
                    if not dry:
                        form.status = TaxForm.Status.APPROVED
                        form.save(update_fields=["status", "updated_at"])

        # forms approved in DB but not covered by the manifest -> would be lost on rebuild
        db_approved = set(
            TaxForm.objects.filter(status=TaxForm.Status.APPROVED)
            .values_list("form_number", flat=True)
        )
        unmanaged = sorted(db_approved - manifest_keys)

        verb = "WOULD flip" if dry else "Flipped"
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"approve_specs ({'dry-run' if dry else 'applied'}): "
            f"{len(APPROVED_FORMS)} manifest entries"
        ))
        self.stdout.write(f"  {verb} -> approved: {len(flipped)}")
        for fn, old in sorted(flipped):
            self.stdout.write(f"      {fn}  ({old} -> approved)")
        self.stdout.write(f"  already approved: {len(already)}")
        if missing:
            self.stdout.write(self.style.WARNING(
                f"  ⚠ manifest entries with NO matching form ({len(missing)}): {sorted(missing)}"
            ))
        if unmanaged:
            self.stdout.write(self.style.ERROR(
                f"  ⚠ approved in DB but NOT in manifest ({len(unmanaged)}) — "
                f"would be LOST on rebuild: {unmanaged}"
            ))
        if not APPROVED_FORMS:
            self.stdout.write("  (manifest is empty — nothing to approve yet)")
