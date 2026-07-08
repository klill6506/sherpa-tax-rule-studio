"""Tests for the tax-law-change funnel: ChangeRegisterItem + the change_register /
detect_source_changes management commands (RS front-of-the-front-door)."""
import json
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from sources.models import (
    AuthoritySource, AuthorityVersion, ChangeDetectionSource, ChangeRegisterItem, ChangeStatus,
)


def run(*args):
    out = StringIO()
    call_command(*args, stdout=out, stderr=out)
    return out.getvalue()


@pytest.fixture
def source(db):
    return AuthoritySource.objects.create(
        source_code="REVPROC_2025_23", source_type="official_revenue_procedure",
        source_rank="primary_official", jurisdiction_code="US",
        title="Rev. Proc. 2025-23 — List of Automatic Changes", citation="Rev. Proc. 2025-23",
        issuer="IRS", current_status="active", is_substantive_authority=True, trust_score=9.2,
    )


@pytest.fixture
def current_version(source):
    return AuthorityVersion.objects.create(
        authority_source=source, version_label="TY2025", file_type="pdf",
        checksum_sha256="a" * 64, is_current=True,
    )


@pytest.mark.django_db
class TestChangeRegisterItemModel:
    def test_defaults(self, source):
        it = ChangeRegisterItem.objects.create(change_code="CR-2026-001", title="t", summary="s", authority_source=source)
        assert it.status == ChangeStatus.DETECTED
        assert it.detected_via == ChangeDetectionSource.MANUAL_CLIP
        assert it.jurisdiction_code == "US"
        assert it.affected_forms == [] and it.affected_rule_ids == []
        assert it.is_substantive is None
        assert str(it) == "CR-2026-001 [detected]: t"

    def test_change_code_unique(self, db):
        ChangeRegisterItem.objects.create(change_code="CR-2026-001", title="t", summary="s")
        with pytest.raises(Exception):
            ChangeRegisterItem.objects.create(change_code="CR-2026-001", title="u", summary="v")


@pytest.mark.django_db
class TestChangeRegisterCommand:
    def test_add_then_list(self, source):
        run("change_register", "add", "--title", "Rev Proc 2026-XX", "--summary", "new list",
            "--forms", "3115,4562", "--tax-year", "2026", "--source", "REVPROC_2025_23")
        it = ChangeRegisterItem.objects.get(change_code="CR-2026-001")
        assert it.status == ChangeStatus.DETECTED
        assert it.affected_forms == ["3115", "4562"]
        assert it.tax_year == 2026
        assert it.authority_source == source
        assert "3115" in run("change_register", "list")

    def test_add_sequential_codes(self, db):
        run("change_register", "add", "--title", "a", "--summary", "s")
        run("change_register", "add", "--title", "b", "--summary", "s")
        codes = set(ChangeRegisterItem.objects.values_list("change_code", flat=True))
        assert codes == {"CR-2026-001", "CR-2026-002"}

    def test_add_requires_title_and_summary(self, db):
        with pytest.raises(CommandError):
            run("change_register", "add", "--title", "only title")

    def test_add_unknown_source_errors(self, db):
        with pytest.raises(CommandError):
            run("change_register", "add", "--title", "t", "--summary", "s", "--source", "NOPE")

    def test_full_lifecycle_add_triage_promote(self, db):
        run("change_register", "add", "--title", "t", "--summary", "s", "--forms", "3115")
        run("change_register", "triage", "--code", "CR-2026-001", "--substantive",
            "--forms", "3115,4562", "--notes", "DCN 7 unchanged")
        it = ChangeRegisterItem.objects.get(change_code="CR-2026-001")
        assert it.status == ChangeStatus.TRIAGED
        assert it.is_substantive is True
        assert it.affected_forms == ["3115", "4562"]
        assert it.triage_notes == "DCN 7 unchanged"

        run("change_register", "promote", "--code", "CR-2026-001", "--work-order", "WO-24")
        it.refresh_from_db()
        assert it.status == ChangeStatus.PROMOTED
        assert it.promoted_work_order == "WO-24"
        assert it.promoted_at is not None

    def test_dismiss_path(self, db):
        run("change_register", "add", "--title", "t", "--summary", "s")
        run("change_register", "triage", "--code", "CR-2026-001", "--not-substantive")
        run("change_register", "dismiss", "--code", "CR-2026-001", "--notes", "editorial only")
        it = ChangeRegisterItem.objects.get(change_code="CR-2026-001")
        assert it.status == ChangeStatus.DISMISSED
        assert it.is_substantive is False
        assert it.triage_notes == "editorial only"

    def test_promote_nonsubstantive_blocked(self, db):
        run("change_register", "add", "--title", "t", "--summary", "s")
        run("change_register", "triage", "--code", "CR-2026-001", "--not-substantive")
        with pytest.raises(CommandError):
            run("change_register", "promote", "--code", "CR-2026-001", "--work-order", "WO-24")

    def test_promote_requires_work_order(self, db):
        run("change_register", "add", "--title", "t", "--summary", "s")
        with pytest.raises(CommandError):
            run("change_register", "promote", "--code", "CR-2026-001")

    def test_triage_missing_code_errors(self, db):
        with pytest.raises(CommandError):
            run("change_register", "triage", "--substantive")


@pytest.mark.django_db
class TestDetectSourceChanges:
    def test_manifest_diff_opens_item(self, current_version):
        manifest = {"REVPROC_2025_23": "b" * 64}  # differs from stored "a"*64
        path = "scratchpad/_test_manifest.json"
        import os
        os.makedirs("scratchpad", exist_ok=True)
        with open(path, "w") as fh:
            json.dump(manifest, fh)
        try:
            run("detect_source_changes", "--manifest", path)
            items = ChangeRegisterItem.objects.filter(detected_via=ChangeDetectionSource.CHECKSUM_DIFF)
            assert items.count() == 1
            it = items.first()
            assert it.status == ChangeStatus.DETECTED
            assert it.authority_source == current_version.authority_source
            assert it.authority_version == current_version
        finally:
            os.remove(path)

    def test_unchanged_checksum_opens_nothing(self, current_version):
        manifest = {"REVPROC_2025_23": "a" * 64}  # identical to stored
        path = "scratchpad/_test_manifest2.json"
        import os
        os.makedirs("scratchpad", exist_ok=True)
        with open(path, "w") as fh:
            json.dump(manifest, fh)
        try:
            run("detect_source_changes", "--manifest", path)
            assert ChangeRegisterItem.objects.count() == 0
        finally:
            os.remove(path)

    def test_idempotent_no_double_open(self, current_version):
        manifest = {"REVPROC_2025_23": "b" * 64}
        path = "scratchpad/_test_manifest3.json"
        import os
        os.makedirs("scratchpad", exist_ok=True)
        with open(path, "w") as fh:
            json.dump(manifest, fh)
        try:
            run("detect_source_changes", "--manifest", path)
            run("detect_source_changes", "--manifest", path)  # second run — same candidate
            assert ChangeRegisterItem.objects.filter(detected_via=ChangeDetectionSource.CHECKSUM_DIFF).count() == 1
        finally:
            os.remove(path)

    def test_no_current_version_is_skipped(self, source):
        # source exists but has no is_current AuthorityVersion -> nothing to diff, no crash
        manifest = {"REVPROC_2025_23": "b" * 64}
        path = "scratchpad/_test_manifest4.json"
        import os
        os.makedirs("scratchpad", exist_ok=True)
        with open(path, "w") as fh:
            json.dump(manifest, fh)
        try:
            out = run("detect_source_changes", "--manifest", path)
            assert ChangeRegisterItem.objects.count() == 0
            assert "no-current-version" in out
        finally:
            os.remove(path)

    def test_requires_an_input(self, db):
        with pytest.raises(CommandError):
            run("detect_source_changes")

    def test_dry_run_opens_nothing(self, current_version):
        manifest = {"REVPROC_2025_23": "c" * 64}
        path = "scratchpad/_test_manifest5.json"
        import os
        os.makedirs("scratchpad", exist_ok=True)
        with open(path, "w") as fh:
            json.dump(manifest, fh)
        try:
            out = run("detect_source_changes", "--manifest", path, "--dry-run")
            assert ChangeRegisterItem.objects.count() == 0
            assert "DIFF" in out
        finally:
            os.remove(path)
