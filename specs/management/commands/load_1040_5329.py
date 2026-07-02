"""Form 5329 — flow assertions ONLY (no form spec authored in Rule Studio yet).

The 1040-side Form 5329 unit (tts tag `1040-5329-full-complete`) was built with
its six flow assertions merged directly into the tts canonical gate file
(server/specs/flow_assertions_1040.json). This loader transcribes those six
Ken-approved assertions VERBATIM so RS's database matches the canonical file
and routine re-exports stay clean (REVIEW_QUEUE 2026-07-01, resolved 2026-07-02:
"tts file canonical; re-seed RS").

No FormRule/FormLine content is seeded here — authoring the full 5329 spec in
Rule Studio remains open work and gets its own READY_TO_SEED review when done.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from specs.models import FlowAssertion


FLOW_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1040-5329-01", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "All parts sum to the owner total (-> Schedule 2 line 8)",
     "description": "Validates compute_5329_full. Bug it catches: a part total dropped from the owner total / Sch 2 line 8.",
     "definition": {"kind": "formula_check", "form": "5329", "formula": "total = L4 + L8 + L17 + L25 + L33 + L41 + L49 + L51 + L55"},
     "sort_order": 1},
    {"assertion_id": "FA-1040-5329-02", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Schedule 2 line 8 = SUM of BOTH owners' Form 5329 totals (dual)",
     "description": "Validates compute_5329_db. Bug it catches: only one owner's 5329 counted, or the sum not written to Sch 2 line 8.",
     "definition": {"kind": "flow_assertion", "form": "5329", "formula": "compute_5329_db: SCH_2.L8 = sum over OWNERS of compute_5329_full(...)['total']"},
     "sort_order": 2},
    {"assertion_id": "FA-1040-5329-03", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Excess-contribution 6% smaller-of cap binds (Parts III-VIII)",
     "description": "Validates the excess-part chain. Bug it catches: the 12/31 value cap ignored, or a blank value zeroing the tax.",
     "definition": {"kind": "reconciliation", "form": "5329", "formula": "Lxx = 6% x min(total excess, 12/31 value); blank value -> no cap (full excess)"},
     "sort_order": 3},
    {"assertion_id": "FA-1040-5329-04", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part IX SECURE 2.0 split (10% window / 25% other)",
     "description": "Validates Part IX. Bug it catches: the window/other buckets swapped, or one rate applied to both.",
     "definition": {"kind": "formula_check", "form": "5329", "formula": "54a = 10% x max(0, 52a-53a); 54b = 25% x max(0, 52b-53b); 55 = 54a+54b"},
     "sort_order": 4},
    {"assertion_id": "FA-1040-5329-05", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Statutory rates pinned + the D_5329_* diagnostics registered",
     "description": "Validates the constants + the no-silent-gap diagnostics. Bug it catches: a rate drift or a diagnostic dropped.",
     "definition": {"kind": "gating_check", "form": "5329", "formula": "rates 6%/10%/25%; D_5329_001..005 in RULES_RETIREMENT"},
     "sort_order": 5},
    {"assertion_id": "FA-1040-5329-06", "assertion_type": "flow_assertion", "entity_types": ["1040"],
     "title": "Part I 10% / 25% SIMPLE early-distribution rate",
     "description": "Validates Part I. Bug it catches: the SIMPLE 25% rate not applied, or L3 not floored at 0.",
     "definition": {"kind": "formula_check", "form": "5329", "formula": "L3 = max(0, L1-L2); L4 = (0.25 if SIMPLE else 0.10) x L3"},
     "sort_order": 6},
]


class Command(BaseCommand):
    help = (
        "Seed the six Form 5329 flow assertions (transcribed from the tts "
        "canonical gate file). FA-only — no form spec content."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self.stdout.write(self.style.MIGRATE_HEADING(
            "Loading Form 5329 flow assertions"))
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(
                assertion_id=a.pop("assertion_id"), defaults=a,
            )
        self.stdout.write(f"  {len(FLOW_ASSERTIONS)} flow assertions")
        self.stdout.write(f"FlowAssertions total: {FlowAssertion.objects.count()}")
