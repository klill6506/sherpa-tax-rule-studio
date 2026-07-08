"""Throwaway-SQLite validation for load_1041_flow_assertions (S-11 leg 8a).

Checks: the loader seeds cleanly; every assertion_id <= 20 chars (the Postgres
varchar(20) cap SQLite ignores); entity_types carry '1041'; the 16 expected ids
are present, active, and idempotent on a second run.

Run: poetry run python scratchpad/validate_1041_fa.py
"""
import os
import sys

PROJECT_ROOT = r"D:\dev\sherpa-tax-rule-studio"
sys.path.insert(0, PROJECT_ROOT)

SQLITE_PATH = os.path.join(PROJECT_ROOT, "scratchpad", "validate_1041_fa.sqlite3")
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from specs.models import FlowAssertion  # noqa: E402

call_command("migrate", verbosity=0, run_syncdb=True)
call_command("load_1041_flow_assertions", verbosity=1)
call_command("load_1041_flow_assertions", verbosity=0)  # idempotency

EXPECTED = [
    "FA-1041-TOTINC", "FA-1041-ATI", "FA-1041-DNI", "FA-1041-IDD",
    "FA-1041-TIERS", "FA-1041-EXEMPT", "FA-1041-TAXINC", "FA-1041-RATES",
    "FA-1041-CGRATE", "FA-1041-TOTTAX", "FA-1041-ESBT", "FA-1041-SETTLE",
    "FA-K1041-CHAR", "FA-K1041-SUM", "GATE-1041-DEFERS", "FA-1041-GA501",
    "FA-K1041-FINYR",
]
EXPECTED_STAGED = ["FA-1041-NIIT", "FA-K1041-NIIT"]

errors = []
qs = FlowAssertion.objects.filter(entity_types__contains="1041")
have = {a.assertion_id: a for a in FlowAssertion.objects.all()}
for aid in EXPECTED:
    a = have.get(aid)
    if a is None:
        errors.append(f"MISSING: {aid}")
        continue
    if len(aid) > 20:
        errors.append(f"ID TOO LONG (> varchar(20)): {aid}")
    if "1041" not in a.entity_types:
        errors.append(f"{aid}: entity_types missing '1041': {a.entity_types}")
    if a.status != "active":
        errors.append(f"{aid}: status {a.status} (expected active)")
    if not a.definition:
        errors.append(f"{aid}: empty definition")

for aid in EXPECTED_STAGED:
    a = have.get(aid)
    if a is None:
        errors.append(f"MISSING STAGED: {aid}")
    elif a.status != "draft":
        errors.append(f"{aid}: status {a.status} (expected draft/staged)")

count = FlowAssertion.objects.count()
expected_total = len(EXPECTED) + len(EXPECTED_STAGED)
if count != expected_total:
    errors.append(f"count {count} != {expected_total} (idempotency or stray rows)")

if errors:
    print("FAIL")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print(f"OK — {len(EXPECTED)} active + {len(EXPECTED_STAGED)} staged, ids <= 20, entity_types ['1041'], idempotent.")
