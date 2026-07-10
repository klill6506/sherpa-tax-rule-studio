"""Scoped prod seed for the 8825 Dec-2025 renumber (2026-07-10).

Runs ONLY Command._load_sources + Command._load_8825 from load_remaining_1120s —
NOT the whole command, because its _expand_4562 owns 4562 R010-R013 and R011
collides with the later load_4562_section179_carryover amend (re-running the
full command would stomp the carryover loader's R011 on prod). Full rebuilds
stay correct via seed_all's base-then-amend ordering.

Run: poetry run python scratchpad/seed_8825_renumber.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.db import transaction  # noqa: E402
from specs.management.commands.load_remaining_1120s import Command  # noqa: E402

cmd = Command()
with transaction.atomic():
    sources = cmd._load_sources()
    cmd._load_8825(sources)
print("8825 renumber seeded (scoped).")
