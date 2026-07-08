"""Shared helpers for the change-register funnel commands (change_register /
detect_source_changes / fetch_federal_register)."""
from sources.models import ChangeRegisterItem


def next_change_code(year: int) -> str:
    """CR-<year>-<zero-padded seq>, sequential within the year."""
    prefix = f"CR-{year}-"
    seqs = []
    for c in ChangeRegisterItem.objects.filter(change_code__startswith=prefix).values_list("change_code", flat=True):
        tail = c.rsplit("-", 1)[-1]
        if tail.isdigit():
            seqs.append(int(tail))
    return f"{prefix}{(max(seqs) + 1) if seqs else 1:03d}"


def parse_csv(val):
    """'a, b ,c' -> ['a','b','c']; falsy -> []."""
    return [v.strip() for v in val.split(",") if v.strip()] if val else []
