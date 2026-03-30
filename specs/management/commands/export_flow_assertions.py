"""Export flow assertions as JSON for tts-tax-app consumption."""
import json
from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from django.db.models import Q

from specs.models import FlowAssertion


class Command(BaseCommand):
    help = "Export flow assertions as JSON"

    def add_arguments(self, parser):
        parser.add_argument("--entity-type", default="1120S")
        parser.add_argument("--output", default="flow_assertions.json")

    def handle(self, *args, **options):
        entity_type = options["entity_type"]
        qs = FlowAssertion.objects.filter(status="active")
        if entity_type:
            qs = qs.filter(Q(entity_types__contains=[entity_type]) | Q(entity_types=[]))

        assertions = []
        for a in qs.order_by("sort_order", "assertion_id"):
            assertions.append({
                "assertion_id": a.assertion_id,
                "title": a.title,
                "description": a.description,
                "assertion_type": a.assertion_type,
                "entity_types": a.entity_types,
                "definition": a.definition,
                "bug_reference": a.bug_reference,
                "status": a.status,
            })

        output = {
            "export_version": "1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "entity_type": entity_type,
            "assertion_count": len(assertions),
            "assertions": assertions,
        }

        path = options["output"]
        with open(path, "w") as f:
            json.dump(output, f, indent=2)

        self.stdout.write(self.style.SUCCESS(f"Exported {len(assertions)} assertions to {path}"))
