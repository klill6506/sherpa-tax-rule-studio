"""detect_source_changes — the checksum-diff arm of the change-register funnel.

Compares a CANDIDATE checksum for each authority source (from a re-fetch) against the checksum
stored on that source's current AuthorityVersion (is_current=True). A mismatch = the source moved
-> open a DETECTED ChangeRegisterItem (idempotent: it won't double-open for the same new checksum).

Candidate checksums come from one of:
  --manifest <path.json>   a JSON object { "<source_code>": "<sha256>", ... }  (e.g. from a fetch job)
  --from-files             recompute sha256 from each current AuthorityVersion's local file_path

This v1 does NOT fetch over the network itself (that's the FEED_POLL follow-up); it diffs checksums
you supply, so it is deterministic and testable. It also flags sources that have NO current version
(nothing to compare against) so the feed coverage gap is visible rather than silent.

Usage:
  manage.py detect_source_changes --manifest scratchpad/latest_checksums.json
  manage.py detect_source_changes --from-files
  manage.py detect_source_changes --manifest ... --dry-run    # report only, open nothing
"""
import hashlib
import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from sources.change_register_helpers import next_change_code as _next_change_code
from sources.models import (
    AuthoritySource, AuthorityVersion, ChangeDetectionSource, ChangeRegisterItem, ChangeStatus,
)


def _sha256_file(path: str) -> str | None:
    if not path or not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class Command(BaseCommand):
    help = "Detect moved authority sources by diffing candidate checksums against the current AuthorityVersion."

    def add_arguments(self, parser):
        parser.add_argument("--manifest", help="JSON file: { source_code: sha256 }.")
        parser.add_argument("--from-files", action="store_true", help="Recompute sha256 from each current version's file_path.")
        parser.add_argument("--dry-run", action="store_true", help="Report diffs; open nothing.")

    def handle(self, *args, **o):
        if not o.get("manifest") and not o.get("from_files"):
            raise CommandError("Provide --manifest <path.json> or --from-files.")
        manifest = {}
        if o.get("manifest"):
            if not os.path.exists(o["manifest"]):
                raise CommandError(f"Manifest not found: {o['manifest']}")
            with open(o["manifest"], encoding="utf-8") as fh:
                manifest = json.load(fh)

        opened, unchanged, no_version, skipped_existing, no_candidate = 0, 0, 0, 0, 0
        year = timezone.now().year

        for src in AuthoritySource.objects.all():
            current = AuthorityVersion.objects.filter(authority_source=src, is_current=True).first()
            if not current:
                no_version += 1
                continue
            # candidate checksum: manifest wins, else recompute from the current version's file
            candidate = manifest.get(src.source_code)
            if candidate is None and o.get("from_files"):
                candidate = _sha256_file(current.file_path)
            if not candidate:
                no_candidate += 1
                continue
            if current.checksum_sha256 and candidate == current.checksum_sha256:
                unchanged += 1
                continue
            # a diff (or no stored checksum to compare) — but don't re-open for the same candidate
            ext_ref = f"checksum:{candidate}"
            dupe = ChangeRegisterItem.objects.filter(
                authority_source=src, detected_via=ChangeDetectionSource.CHECKSUM_DIFF, external_ref=ext_ref,
            ).exists()
            if dupe:
                skipped_existing += 1
                continue
            if o.get("dry_run"):
                self.stdout.write(self.style.WARNING(
                    f"DIFF  {src.source_code}: stored {(current.checksum_sha256 or '(none)')[:16]} -> candidate {candidate[:16]}"))
                opened += 1
                continue
            with transaction.atomic():
                code = _next_change_code(year)
                ChangeRegisterItem.objects.create(
                    change_code=code, title=f"Source moved: {src.source_code} ({src.title[:120]})",
                    summary=(f"Checksum diff on {src.source_code}: current AuthorityVersion "
                             f"'{current.version_label}' checksum {(current.checksum_sha256 or '(none)')} "
                             f"!= candidate {candidate}. Re-verify the source and any dependent rules."),
                    jurisdiction_code=src.jurisdiction_code or "US",
                    detected_via=ChangeDetectionSource.CHECKSUM_DIFF, status=ChangeStatus.DETECTED,
                    authority_source=src, authority_version=current, external_ref=ext_ref,
                )
                opened += 1
                self.stdout.write(self.style.SUCCESS(f"DETECTED {code}: {src.source_code} checksum moved"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"detect_source_changes: {opened} opened / {unchanged} unchanged / "
                          f"{skipped_existing} already-open / {no_candidate} no-candidate / {no_version} no-current-version")
        if no_version:
            self.stdout.write(f"  NOTE: {no_version} source(s) have no current AuthorityVersion — nothing to diff (feed-coverage gap).")
        self.stdout.write("=" * 60)
