"""One-off integrity check for load_1040_spine.py content lists (no DB writes)."""
from specs.management.commands import load_1040_spine as m

rules = {r["rule_id"] for r in m.FORM_RULES}
linked = {t[0] for t in m.RULE_AUTHORITY_LINKS}
srcs = {s["source_code"] for s in m.AUTHORITY_SOURCES} | set(m.EXISTING_SOURCES_TO_REFERENCE)
link_srcs = {t[1] for t in m.RULE_AUTHORITY_LINKS}

print("rules:", len(m.FORM_RULES), "facts:", len(m.FORM_FACTS), "lines:", len(m.FORM_LINES))
print("diags:", len(m.FORM_DIAGNOSTICS), "scenarios:", len(m.TEST_SCENARIOS),
      "assertions:", len(m.FLOW_ASSERTIONS), "links:", len(m.RULE_AUTHORITY_LINKS),
      "new sources:", len(m.AUTHORITY_SOURCES))
print("uncited rules:", sorted(rules - linked) or "NONE")
print("links to unknown rules:", sorted(linked - rules) or "NONE")
print("links to unknown sources:", sorted(link_srcs - srcs) or "NONE")
print("dup rule ids:", len(m.FORM_RULES) - len(rules))
print("dup facts:", len(m.FORM_FACTS) - len({f["fact_key"] for f in m.FORM_FACTS}))
print("dup lines:", len(m.FORM_LINES) - len({l["line_number"] for l in m.FORM_LINES}))
print("dup diags:", len(m.FORM_DIAGNOSTICS) - len({d["diagnostic_id"] for d in m.FORM_DIAGNOSTICS}))
print("dup assertions:", len(m.FLOW_ASSERTIONS) - len({a["assertion_id"] for a in m.FLOW_ASSERTIONS}))
print("dup scenarios:", len(m.TEST_SCENARIOS) - len({t["scenario_name"] for t in m.TEST_SCENARIOS}))

# AuthorityExcerpt field whitelist check
allowed = {"excerpt_label", "location_reference", "excerpt_text", "summary_text",
           "topic_tags", "line_or_page_start", "line_or_page_end",
           "effective_year_start", "effective_year_end", "is_key_excerpt"}
bad = []
for s in m.AUTHORITY_SOURCES:
    for e in s.get("excerpts", []):
        extra = set(e) - allowed
        if extra:
            bad.append((s["source_code"], e["excerpt_label"], extra))
for code, e in m.NEW_EXCERPTS_ON_EXISTING:
    extra = set(e) - allowed
    if extra:
        bad.append((code, e["excerpt_label"], extra))
print("excerpt field violations:", bad or "NONE")

# AuthoritySource choice checks
from sources.models import SourceRank, SourceStatus, SourceType
st = {c[0] for c in SourceType.choices}
sr = {c[0] for c in SourceRank.choices}
ss = {c[0] for c in SourceStatus.choices}
viol = [(s["source_code"], s["source_type"], s["source_rank"], s["current_status"])
        for s in m.AUTHORITY_SOURCES
        if s["source_type"] not in st or s["source_rank"] not in sr or s["current_status"] not in ss]
print("source choice violations:", viol or "NONE")
