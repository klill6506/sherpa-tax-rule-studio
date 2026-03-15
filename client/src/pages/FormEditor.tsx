import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import TopBar from "../components/TopBar";
import DiagnosticsTab from "../components/tabs/DiagnosticsTab";
import FactsTab from "../components/tabs/FactsTab";
import LineMapTab from "../components/tabs/LineMapTab";
import OverviewTab from "../components/tabs/OverviewTab";
import RulesTab from "../components/tabs/RulesTab";
import SourcesTab from "../components/tabs/SourcesTab";
import StateConformityTab from "../components/tabs/StateConformityTab";
import TestsTab from "../components/tabs/TestsTab";
import type { TaxForm } from "../types";

const TABS = [
  { key: "overview", label: "Overview" },
  { key: "facts", label: "Facts" },
  { key: "rules", label: "Rules" },
  { key: "lines", label: "Line Map" },
  { key: "diagnostics", label: "Diagnostics" },
  { key: "tests", label: "Tests" },
  { key: "sources", label: "Sources" },
  { key: "conformity", label: "State Conformity" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

/* eslint-disable @typescript-eslint/no-explicit-any */
function exportToMarkdown(data: any): string {
  const m = data.metadata;
  const lines: string[] = [];
  lines.push(`# Form ${m.form_number} — ${m.form_title}`);
  lines.push(`**Jurisdiction:** ${m.jurisdiction} | **Tax Year:** ${m.tax_year} | **Version:** ${m.version} | **Status:** ${m.status}`);
  lines.push(`**Entity Types:** ${(m.entity_types ?? []).join(", ")}`);
  lines.push("");

  // Facts
  if (data.facts?.length) {
    lines.push("## Facts (Inputs)");
    lines.push("| Fact Key | Label | Type | Required | Default | Validation |");
    lines.push("|----------|-------|------|----------|---------|------------|");
    for (const f of data.facts) {
      lines.push(`| ${f.fact_key} | ${f.label} | ${f.data_type} | ${f.required ? "Yes" : "No"} | ${f.default_value ?? "—"} | ${f.validation_rule ?? "—"} |`);
    }
    lines.push("");
  }

  // Rules
  if (data.rules?.length) {
    lines.push("## Rules");
    for (const r of data.rules) {
      lines.push(`### ${r.rule_id}: ${r.title}`);
      lines.push(`**Type:** ${r.rule_type} | **Precedence:** ${r.precedence}`);
      if (r.description) lines.push(`\n${r.description}`);
      if (r.formula) lines.push(`\n**Formula:** \`${r.formula}\``);
      if (r.inputs?.length) lines.push(`**Inputs:** ${r.inputs.join(", ")}`);
      if (r.outputs?.length) lines.push(`**Outputs:** ${r.outputs.join(", ")}`);
      if (r.exceptions) lines.push(`**Exceptions:** ${r.exceptions}`);
      if (r.authorities?.length) {
        lines.push("\n**Authorities:**");
        for (const a of r.authorities) {
          lines.push(`- ${a.citation ?? a.source_code} — [${a.support_level}] ${a.relevance_note ?? ""}`);
        }
      }
      lines.push("");
    }
  }

  // Line Map
  if (data.line_map?.length) {
    lines.push("## Line Map");
    lines.push("| Line | Description | Type | Calculation | Source Facts | Source Rules | Flows To |");
    lines.push("|------|-------------|------|-------------|-------------|-------------|----------|");
    for (const l of data.line_map) {
      lines.push(`| ${l.line_number} | ${l.description ?? ""} | ${l.line_type} | ${l.calculation ?? "—"} | ${(l.source_facts ?? []).join(", ") || "—"} | ${(l.source_rules ?? []).join(", ") || "—"} | ${l.destination_form ?? "—"} |`);
    }
    lines.push("");
  }

  // Diagnostics
  if (data.diagnostics?.length) {
    lines.push("## Diagnostics");
    for (const d of data.diagnostics) {
      lines.push(`- **${d.diagnostic_id}** [${d.severity}]: ${d.title}`);
      if (d.condition) lines.push(`  - Condition: ${d.condition}`);
      if (d.message) lines.push(`  - Message: ${d.message}`);
    }
    lines.push("");
  }

  // Tests
  if (data.tests?.length) {
    lines.push("## Test Scenarios");
    for (const t of data.tests) {
      lines.push(`### ${t.scenario_name} (${t.scenario_type})`);
      lines.push(`**Inputs:** \`${JSON.stringify(t.inputs)}\``);
      lines.push(`**Expected:** \`${JSON.stringify(t.expected_outputs)}\``);
      lines.push("");
    }
  }

  // Authority Sources
  if (data.authority_sources?.length) {
    lines.push("## Authority Sources");
    for (const s of data.authority_sources) {
      lines.push(`### ${s.source_code}: ${s.title}`);
      lines.push(`**Type:** ${s.source_type} | **Rank:** ${s.source_rank} | **Jurisdiction:** ${s.jurisdiction_code}`);
      if (s.citation) lines.push(`**Citation:** ${s.citation}`);
      if (s.topics?.length) lines.push(`**Topics:** ${s.topics.join(", ")}`);
      if (s.excerpts?.length) {
        for (const e of s.excerpts) {
          lines.push(`\n> **${e.excerpt_label ?? "Excerpt"}${e.is_key_excerpt ? " ★" : ""}**`);
          lines.push(`> ${(e.excerpt_text ?? "").slice(0, 200)}${(e.excerpt_text ?? "").length > 200 ? "..." : ""}`);
          if (e.summary_text) lines.push(`> *Summary:* ${e.summary_text}`);
        }
      }
      lines.push("");
    }
  }

  // State Conformity
  lines.push("## State Conformity");
  if (data.state_conformity) {
    const sc = data.state_conformity;
    lines.push(`**${sc.jurisdiction_code}** TY${sc.tax_year} — **${sc.conformity_type}**`);
    if (sc.federal_reference_note) lines.push(`\n${sc.federal_reference_note}`);
    if (sc.summary) lines.push(`\n${sc.summary}`);
    if (sc.decoupled_items?.length) {
      lines.push("\n### Decoupled Items");
      for (const item of sc.decoupled_items) {
        lines.push(`- **${item.item}**`);
        lines.push(`  - Federal: ${item.federal_treatment}`);
        lines.push(`  - State: ${item.state_treatment}`);
        if (item.notes) lines.push(`  - Notes: ${item.notes}`);
      }
    }
  } else {
    lines.push("N/A (Federal form)");
  }

  return lines.join("\n");
}
/* eslint-enable @typescript-eslint/no-explicit-any */

function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function FormEditor() {
  const { formId } = useParams<{ formId: string }>();
  const [form, setForm] = useState<TaxForm | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");

  const fetchForm = useCallback(async () => {
    if (!formId) return;
    try {
      const data = await api.get<TaxForm>(`/forms/${formId}/`);
      setForm(data);
    } catch (err) {
      console.error("Failed to fetch form:", err);
    } finally {
      setLoading(false);
    }
  }, [formId]);

  useEffect(() => {
    setLoading(true);
    void fetchForm();
  }, [fetchForm]);

  async function handleStatusChange(status: TaxForm["status"]) {
    if (!formId || !form) return;
    try {
      const updated = await api.patch<TaxForm>(`/forms/${formId}/`, { status });
      setForm(updated);
    } catch (err) {
      console.error("Failed to update status:", err);
    }
  }

  async function fetchExportData() {
    if (!formId) return null;
    try {
      return await api.get<unknown>(`/forms/${formId}/export/`);
    } catch (err) {
      console.error("Export failed:", err);
      return null;
    }
  }

  async function handleExportJson() {
    const data = await fetchExportData();
    if (!data || !form) return;
    const filename = `${form.form_number}_TY${form.tax_year}_v${form.version}_spec.json`;
    downloadFile(JSON.stringify(data, null, 2), filename, "application/json");
  }

  async function handleExportMarkdown() {
    const data = await fetchExportData();
    if (!data || !form) return;
    const md = exportToMarkdown(data);
    const filename = `${form.form_number}_TY${form.tax_year}_v${form.version}_spec.md`;
    downloadFile(md, filename, "text/markdown");
  }

  if (loading) {
    return <div className="flex items-center justify-center h-full text-gray-400">Loading...</div>;
  }

  if (!form) {
    return <div className="flex items-center justify-center h-full text-red-500">Form not found.</div>;
  }

  const visibleTabs = form.jurisdiction.toLowerCase() === "federal"
    ? TABS.filter((t) => t.key !== "conformity")
    : TABS;

  return (
    <div className="flex flex-col h-full">
      <TopBar form={form} onStatusChange={handleStatusChange} onExportJson={handleExportJson} onExportMarkdown={handleExportMarkdown} />

      <div className="border-b border-gray-200 bg-white px-6">
        <nav className="flex gap-1 -mb-px">
          {visibleTabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="flex-1 overflow-auto p-6">
        {activeTab === "overview" && <OverviewTab form={form} onUpdate={fetchForm} />}
        {activeTab === "facts" && <FactsTab formId={form.id} />}
        {activeTab === "rules" && <RulesTab formId={form.id} />}
        {activeTab === "lines" && <LineMapTab formId={form.id} />}
        {activeTab === "diagnostics" && <DiagnosticsTab formId={form.id} />}
        {activeTab === "tests" && <TestsTab formId={form.id} />}
        {activeTab === "sources" && <SourcesTab formId={form.id} formNumber={form.form_number} />}
        {activeTab === "conformity" && <StateConformityTab jurisdiction={form.jurisdiction} taxYear={form.tax_year} />}
      </div>
    </div>
  );
}
