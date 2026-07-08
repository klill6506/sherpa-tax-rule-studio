"""fetch_irb — FEED_POLL leg 2 of the change-register funnel.

Scrapes the IRS Internal Revenue Bulletin (IRB) index page and opens a DETECTED ChangeRegisterItem
per NEW weekly bulletin. The IRB is where SUB-REGULATORY guidance lives — Revenue Procedures,
Notices, Revenue Rulings, Announcements (e.g. the annual Form 3115 automatic-change list, indexed-
amount updates) — which do NOT publish in the Federal Register, so `fetch_federal_register` misses them.

Detection is BULLETIN-LEVEL (one item per weekly IRB), not item-level: a bulletin bundles many
Rev.Procs/Notices, and parsing each bulletin's PDF for individual items is fragile. Triage drills into
the bulletin to decide which items matter. Item-level parsing is a future refinement.

Why scrape (not an API): govinfo has no IRB collection, and irs.gov exposes no IRB API — the index
page is the machine-readable surface. Verified 2026-07-08: the index lists 25 bulletins/page, each as
`<a href="/pub/irs-irbs/irbYY-NN.pdf">Internal Revenue Bulletin YYYY-NN</a>` (a stable URL + title
pattern). irs.gov needs a browser User-Agent (returns 200 with one). stdlib urllib (no requests dep).

Usage:
  manage.py fetch_irb                          # most recent --limit bulletins (default 5)
  manage.py fetch_irb --since-bulletin 2026-20  # only bulletins numbered >= 2026-20
  manage.py fetch_irb --limit 10
  manage.py fetch_irb --dry-run                 # report; open nothing
"""
import re
import urllib.error
import urllib.request

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from sources.change_register_helpers import next_change_code
from sources.models import ChangeDetectionSource, ChangeRegisterItem, ChangeStatus

IRB_INDEX_URL = "https://www.irs.gov/internal-revenue-bulletins"
IRB_HOST = "https://www.irs.gov"
USER_AGENT = "Mozilla/5.0 (compatible; sherpa-tax-rule-studio change-register; +https://kenlill.com)"
DEFAULT_LIMIT = 5

# <a href="/pub/irs-irbs/irb26-28.pdf" ...>Internal Revenue Bulletin 2026-28</a>
BULLETIN_RE = re.compile(
    r'href="(?P<href>/pub/irs-irbs/irb\d{2}-\d{1,3}\.pdf)"[^>]*>\s*Internal Revenue Bulletin\s+(?P<num>\d{4}-\d{1,3})\s*<',
    re.IGNORECASE)


def _http_get_text(url: str) -> str:
    """Isolated network call — monkeypatched in tests so the suite never hits the network."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (fixed https host)
        return resp.read().decode("utf-8", errors="replace")


def _bulletin_key(num: str) -> tuple:
    """'2026-7' -> (2026, 7) for chronological comparison/sorting."""
    year, wk = num.split("-", 1)
    return (int(year), int(wk))


def parse_bulletins(html: str) -> list:
    """Return [(bulletin_number, pdf_url)] de-duplicated, newest first."""
    seen, out = set(), []
    for m in BULLETIN_RE.finditer(html):
        num = m.group("num")
        if num in seen:
            continue
        seen.add(num)
        out.append((num, IRB_HOST + m.group("href")))
    out.sort(key=lambda t: _bulletin_key(t[0]), reverse=True)
    return out


class Command(BaseCommand):
    help = "Open DETECTED change-register items from newly published Internal Revenue Bulletins (FEED_POLL leg 2)."

    def add_arguments(self, parser):
        parser.add_argument("--since-bulletin", help="Only bulletins numbered >= this (YYYY-NN). Overrides --limit.")
        parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Take the N most recent bulletins (default 5).")
        parser.add_argument("--dry-run", action="store_true", help="Report; open nothing.")

    def handle(self, *args, **o):
        self.stdout.write(self.style.MIGRATE_HEADING("\nInternal Revenue Bulletin — index scan\n"))
        try:
            html = _http_get_text(IRB_INDEX_URL)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            raise CommandError(f"IRB index fetch failed: {e!r}")

        bulletins = parse_bulletins(html)
        if not bulletins:
            raise CommandError("Parsed 0 bulletins — the IRB index page layout may have changed (update BULLETIN_RE).")

        if o.get("since_bulletin"):
            try:
                floor = _bulletin_key(o["since_bulletin"])
            except (ValueError, IndexError):
                raise CommandError("--since-bulletin must look like YYYY-NN (e.g. 2026-20).")
            selected = [b for b in bulletins if _bulletin_key(b[0]) >= floor]
        else:
            selected = bulletins[: o["limit"]]

        opened, skipped = 0, 0
        year = timezone.now().year
        for num, pdf_url in selected:
            ext_ref = f"IRB-{num}"
            if ChangeRegisterItem.objects.filter(external_ref=ext_ref).exists():
                skipped += 1
                continue
            title = f"Internal Revenue Bulletin {num} published"
            summary = (f"[Internal Revenue Bulletin {num}] A new weekly IRB is published. It may contain Revenue "
                       f"Procedures, Notices, Revenue Rulings, or Announcements relevant to authored rules (e.g. an "
                       f"automatic-change list update, indexed amounts). Review the bulletin and triage the specific "
                       f"items.\nIRB {num}: {pdf_url}")
            if o.get("dry_run"):
                self.stdout.write(self.style.WARNING(f"NEW  IRB {num}  {pdf_url}"))
                opened += 1
                continue
            with transaction.atomic():
                code = next_change_code(year)
                ChangeRegisterItem.objects.create(
                    change_code=code, title=title, summary=summary, jurisdiction_code="US",
                    detected_via=ChangeDetectionSource.FEED_POLL, status=ChangeStatus.DETECTED, external_ref=ext_ref,
                )
                opened += 1
                self.stdout.write(self.style.SUCCESS(f"DETECTED {code}: IRB {num}"))

        self.stdout.write("\n" + "=" * 60)
        verb = "would open" if o.get("dry_run") else "opened"
        self.stdout.write(f"fetch_irb: {len(bulletins)} on index / {len(selected)} selected / "
                          f"{opened} {verb} / {skipped} already-known")
        self.stdout.write("=" * 60)
