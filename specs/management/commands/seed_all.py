"""Canonical full-rebuild orchestrator — runs every loader in dependency order.

This is the single command that reconstructs the entire RS spec database from the
loaders in source control. It exists because the individual `load_*` commands have
ordering dependencies (authority sources before forms; base forms before AMEND
loaders; flow assertions after all forms) that were previously tribal knowledge —
there was no one entrypoint, so a fresh DB could not be rebuilt reproducibly.

Phases:
  1. Sources    — feeds/topics + federal authority sources (forms reference these)
  2. Specs      — every specs `load_*` loader (forms/rules/lines/diagnostics/scenarios)
  3. Amends     — loaders that MUTATE a pre-existing base spec (must run after step 2)
  4. Flow       — flow assertions (reference forms across the whole DB)

Loaders are discovered dynamically, so new `load_*` commands are picked up
automatically. AMEND loaders and non-seed commands are listed explicitly below.

Idempotent: every loader uses update_or_create, so re-running is safe. NOTE this
brings a stale DB UP to the loaders (adds missing rules) but does NOT delete
orphaned rows left by refactored loaders — see reconstructability_check.md.

Usage:
  poetry run python manage.py seed_all            # run it
  poetry run python manage.py seed_all --dry-run  # print the plan only
"""
from django.core.management import call_command, get_commands
from django.core.management.base import BaseCommand

# Loaders that amend an existing base spec and must run AFTER all base forms exist.
AMEND_LOADERS = ["load_1040_form_3800"]

# specs commands that are NOT part of the seed rebuild.
NON_SEED = {"export_flow_assertions", "seed_flow_assertions", "seed_all", *AMEND_LOADERS}

# Phase 1 (sources app) and phase 4 (flow assertions) — explicit, order matters.
SOURCE_LOADERS = ["seed_sources", "load_all_federal", "load_1120s_family"]
FLOW_LOADERS = ["seed_flow_assertions"]


class Command(BaseCommand):
    help = "Reconstruct the entire RS spec DB from loaders, in dependency order."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Print the ordered loader plan without running anything.",
        )

    def handle(self, *_args, **opts):
        registered = get_commands()
        specs_loaders = sorted(
            name
            for name, app in registered.items()
            if app == "specs" and name.startswith("load_") and name not in NON_SEED
        )

        plan = [
            ("1. sources", SOURCE_LOADERS),
            (f"2. specs ({len(specs_loaders)})", specs_loaders),
            ("3. amends", AMEND_LOADERS),
            ("4. flow assertions", FLOW_LOADERS),
        ]

        if opts["dry_run"]:
            self.stdout.write(self.style.MIGRATE_HEADING("seed_all plan (dry run):"))
            for phase, cmds in plan:
                self.stdout.write(f"  {phase}")
                for c in cmds:
                    mark = "" if c in registered else "   [MISSING]"
                    self.stdout.write(f"      - {c}{mark}")
            return

        ran, failed = 0, []
        for phase, cmds in plan:
            self.stdout.write(self.style.MIGRATE_HEADING(f"=== Phase {phase} ==="))
            for c in cmds:
                if c not in registered:
                    failed.append((c, "not registered"))
                    self.stdout.write(self.style.ERROR(f"  [MISSING] {c}"))
                    continue
                try:
                    call_command(c)
                    ran += 1
                    self.stdout.write(self.style.SUCCESS(f"  [OK] {c}"))
                except Exception as e:  # noqa: BLE001 — report, keep going
                    failed.append((c, f"{type(e).__name__}: {e}"))
                    self.stdout.write(self.style.ERROR(f"  [FAIL] {c} -> {e}"))

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING(f"seed_all complete: {ran} OK, {len(failed)} problem(s)"))
        for c, err in failed:
            self.stdout.write(self.style.ERROR(f"  {c}: {err}"))
