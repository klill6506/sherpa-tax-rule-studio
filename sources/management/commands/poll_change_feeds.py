"""poll_change_feeds — the scheduler entry point for the change-register funnel.

ONE command the Render cron job runs on a schedule. It runs every automated FEED_POLL detector
(Federal Register + Internal Revenue Bulletin) RESILIENTLY — a failure in one arm (e.g. a network
blip) is logged and does not stop the others — then reports how many new DETECTED items were opened
and (optionally) pings Pushover so Ken knows to triage.

It changes nothing about the gates: it only fills the register to DETECTED. Triage/promotion/authoring
still run through Ken and the existing front door.

Exit code: 0 if at least one arm succeeded (even if it opened nothing); non-zero only if EVERY arm
errored (so Render surfaces a real outage, not an empty week).

Usage:
  manage.py poll_change_feeds                     # FR (last 8 days) + IRB (last 3 bulletins)
  manage.py poll_change_feeds --fr-lookback-days 8 --irb-limit 3
  manage.py poll_change_feeds --dry-run           # run both arms, open nothing
  manage.py poll_change_feeds --no-irb            # skip an arm

Optional notification: set PUSHOVER_TOKEN + PUSHOVER_USER env vars to get a ping when new items open.
"""
import os
import urllib.parse
import urllib.request

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from sources.models import ChangeRegisterItem

# (command_name, kwargs) for each automated arm. Weekly-friendly defaults with overlap so nothing slips
# through the cracks between runs (idempotency dedups the overlap).
ARMS = [
    ("fetch_federal_register", lambda o: {"lookback_days": o["fr_lookback_days"], "dry_run": o["dry_run"]}),
    ("fetch_irb", lambda o: {"limit": o["irb_limit"], "dry_run": o["dry_run"]}),
]


def _notify(message: str) -> bool:
    """Best-effort Pushover ping; only fires if both env vars are set; never raises."""
    token, user = os.getenv("PUSHOVER_TOKEN"), os.getenv("PUSHOVER_USER")
    if not (token and user):
        return False
    try:
        data = urllib.parse.urlencode(
            {"token": token, "user": user, "title": "RS change register", "message": message}).encode()
        req = urllib.request.Request("https://api.pushover.net/1/messages.json", data=data)
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
            resp.read()
        return True
    except Exception:  # noqa: BLE001 — notification must never break the poll
        return False


class Command(BaseCommand):
    help = "Run all automated change-register feed pollers (Federal Register + IRB) for the scheduler."

    def add_arguments(self, parser):
        parser.add_argument("--fr-lookback-days", type=int, default=8, help="Federal Register lookback (default 8).")
        parser.add_argument("--irb-limit", type=int, default=3, help="IRB: most-recent N bulletins to check (default 3).")
        parser.add_argument("--no-fr", action="store_true", help="Skip the Federal Register arm.")
        parser.add_argument("--no-irb", action="store_true", help="Skip the IRB arm.")
        parser.add_argument("--dry-run", action="store_true", help="Run both arms; open nothing.")

    def handle(self, *args, **o):
        self.stdout.write(self.style.MIGRATE_HEADING("\npoll_change_feeds — automated change-register intake\n"))
        skip = {"fetch_federal_register": o["no_fr"], "fetch_irb": o["no_irb"]}
        results, total_opened = [], 0

        for name, kwargs_fn in ARMS:
            if skip.get(name):
                self.stdout.write(f"— {name}: skipped")
                continue
            before = ChangeRegisterItem.objects.count()
            try:
                call_command(name, stdout=self.stdout, stderr=self.stderr, **kwargs_fn(o))
                opened = 0 if o["dry_run"] else ChangeRegisterItem.objects.count() - before
                results.append((name, True, opened, None))
                total_opened += max(0, opened)
            except Exception as e:  # noqa: BLE001 — one arm must not kill the others
                results.append((name, False, 0, repr(e)))
                self.stderr.write(self.style.ERROR(f"— {name} FAILED: {e!r}"))

        ran = results  # skipped arms never get appended
        ok = [r for r in results if r[1]]

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"poll_change_feeds: {len(ok)}/{len(ran)} arms ok / {total_opened} new item(s) opened"
                          + (" [dry-run]" if o["dry_run"] else ""))
        for name, okflag, opened, err in results:
            self.stdout.write(f"  {'OK ' if okflag else 'ERR'} {name}: "
                              + (f"{opened} opened" if okflag else err))
        self.stdout.write("=" * 60)

        if total_opened and not o["dry_run"]:
            pinged = _notify(f"{total_opened} new tax-law change item(s) detected — triage in the register "
                             f"(change_register list --status detected).")
            self.stdout.write(f"Pushover: {'sent' if pinged else 'not configured (set PUSHOVER_TOKEN/PUSHOVER_USER)'}")

        # Non-zero ONLY if everything errored — a real outage, not a quiet week.
        if ran and not ok:
            raise CommandError("All change-feed arms failed — see errors above.")
