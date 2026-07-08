"""fetch_federal_register — FEED_POLL leg 1 of the change-register funnel.

Queries the public Federal Register API (federalregister.gov, free, no key) for recently published
IRS / Treasury regulatory documents (final RULE + proposed PRORULE) and opens a DETECTED
ChangeRegisterItem for each NEW one (idempotent by the FR document_number, stored in external_ref).

This is the automated intake the CHANGE_REGISTER always wanted: regulatory changes flow in without a
human clip. It still only reaches DETECTED — triage and every downstream step run through the gates.

The FR API carries Treasury/IRS *regulations* (final + proposed rules). Sub-regulatory guidance
(Rev. Procs, Notices, Rev. Ruls — e.g. the annual automatic-change list) publishes in the Internal
Revenue Bulletin, NOT reliably in the FR — those still come via manual clip / the IRB feed (future leg).

Verified 2026-07-08 against the live API: results[] carry document_number / title / type /
publication_date / html_url / abstract / agencies; filter via conditions[agencies][],
conditions[type][], conditions[publication_date][gte]. `requests` is not installed -> stdlib urllib.

Usage:
  manage.py fetch_federal_register                       # IRS RULE+PRORULE, last 7 days
  manage.py fetch_federal_register --since 2026-01-01     # explicit start date
  manage.py fetch_federal_register --lookback-days 30
  manage.py fetch_federal_register --types RULE,PRORULE,NOTICE --agencies internal-revenue-service,treasury-department
  manage.py fetch_federal_register --dry-run              # report; open nothing
"""
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from sources.change_register_helpers import next_change_code
from sources.models import ChangeDetectionSource, ChangeRegisterItem, ChangeStatus

FR_API = "https://www.federalregister.gov/api/v1/documents.json"
DEFAULT_AGENCIES = ["internal-revenue-service"]
DEFAULT_TYPES = ["RULE", "PRORULE"]  # final + proposed Treasury/IRS regulations
DEFAULT_LOOKBACK_DAYS = 7
FR_FIELDS = ["document_number", "title", "type", "publication_date", "html_url", "pdf_url", "abstract", "agencies"]
USER_AGENT = "sherpa-tax-rule-studio change-register (+https://kenlill.com)"


def _build_url(since, types, agencies, per_page) -> str:
    params = [("per_page", str(per_page)), ("order", "oldest"),
              ("conditions[publication_date][gte]", since)]
    params += [("conditions[agencies][]", a) for a in agencies]
    params += [("conditions[type][]", t) for t in types]
    params += [("fields[]", f) for f in FR_FIELDS]
    return f"{FR_API}?{urllib.parse.urlencode(params)}"


def _http_get_json(url: str) -> dict:
    """Isolated network call — monkeypatched in tests so the suite never hits the network."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (fixed https host)
        return json.loads(resp.read().decode("utf-8"))


def fetch_documents(since, types, agencies, per_page=100, max_pages=5):
    """Return (documents, pages_read, truncated). Paginates via the API's next_page_url up to max_pages."""
    url = _build_url(since, types, agencies, per_page)
    docs, pages = [], 0
    while url and pages < max_pages:
        data = _http_get_json(url)
        docs.extend(data.get("results", []))
        url = data.get("next_page_url")
        pages += 1
    return docs, pages, bool(url)  # truncated if a next page still remained at the cap


class Command(BaseCommand):
    help = "Open DETECTED change-register items from recent IRS/Treasury Federal Register documents (FEED_POLL)."

    def add_arguments(self, parser):
        parser.add_argument("--since", help="Start publication date YYYY-MM-DD (default: today - lookback-days).")
        parser.add_argument("--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS)
        parser.add_argument("--types", help=f"Comma FR types (default {','.join(DEFAULT_TYPES)}). e.g. RULE,PRORULE,NOTICE")
        parser.add_argument("--agencies", help=f"Comma FR agency slugs (default {','.join(DEFAULT_AGENCIES)}).")
        parser.add_argument("--per-page", type=int, default=100)
        parser.add_argument("--max-pages", type=int, default=5, help="Safety cap on pagination.")
        parser.add_argument("--dry-run", action="store_true", help="Report; open nothing.")

    def handle(self, *args, **o):
        since = o.get("since") or (timezone.now().date() - timedelta(days=o["lookback_days"])).isoformat()
        types = [t.strip() for t in o["types"].split(",")] if o.get("types") else DEFAULT_TYPES
        agencies = [a.strip() for a in o["agencies"].split(",")] if o.get("agencies") else DEFAULT_AGENCIES

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\nFederal Register — {'/'.join(types)} from {'/'.join(agencies)} since {since}\n"))
        try:
            docs, pages, truncated = fetch_documents(since, types, agencies, o["per_page"], o["max_pages"])
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError) as e:
            raise CommandError(f"Federal Register fetch failed: {e!r}")

        opened, skipped = 0, 0
        year = timezone.now().year
        for d in docs:
            docnum = d.get("document_number")
            if not docnum:
                continue
            if ChangeRegisterItem.objects.filter(external_ref=docnum).exists():
                skipped += 1
                continue
            title = (d.get("title") or f"Federal Register {docnum}")[:255]
            summary = (f"[Federal Register {d.get('type', '?')} · published {d.get('publication_date', '?')}] "
                       f"{d.get('abstract') or d.get('title') or ''}\n"
                       f"FR document {docnum}: {d.get('html_url') or ''}")
            if o.get("dry_run"):
                self.stdout.write(self.style.WARNING(f"NEW  {docnum}  {d.get('publication_date','')}  {title[:80]}"))
                opened += 1
                continue
            with transaction.atomic():
                code = next_change_code(year)
                ChangeRegisterItem.objects.create(
                    change_code=code, title=title, summary=summary, jurisdiction_code="US",
                    detected_via=ChangeDetectionSource.FEED_POLL, status=ChangeStatus.DETECTED,
                    external_ref=docnum,
                )
                opened += 1
                self.stdout.write(self.style.SUCCESS(f"DETECTED {code}: {docnum}  {title[:70]}"))

        self.stdout.write("\n" + "=" * 60)
        verb = "would open" if o.get("dry_run") else "opened"
        self.stdout.write(f"fetch_federal_register: {len(docs)} fetched / {opened} {verb} / {skipped} already-known "
                          f"({pages} page(s))")
        if truncated:
            self.stdout.write(self.style.WARNING(
                f"  ⚠ hit the {o['max_pages']}-page cap — more results remain; narrow --since or raise --max-pages."))
        self.stdout.write("=" * 60)
