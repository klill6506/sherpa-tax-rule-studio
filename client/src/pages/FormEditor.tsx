import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import TopBar from "../components/TopBar";
import DiagnosticsTab from "../components/tabs/DiagnosticsTab";
import FactsTab from "../components/tabs/FactsTab";
import LineMapTab from "../components/tabs/LineMapTab";
import OverviewTab from "../components/tabs/OverviewTab";
import RulesTab from "../components/tabs/RulesTab";
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

function PlaceholderTab({ name }: { name: string }) {
  return (
    <div className="flex items-center justify-center h-64 text-gray-400">
      <p>{name} tab — coming in a future session.</p>
    </div>
  );
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

  async function handleExport() {
    if (!formId) return;
    try {
      const data = await api.get<unknown>(`/forms/${formId}/export/`);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${form?.jurisdiction}_${form?.form_number}_${form?.tax_year}_v${form?.version}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed:", err);
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-full text-gray-400">Loading...</div>;
  }

  if (!form) {
    return <div className="flex items-center justify-center h-full text-red-500">Form not found.</div>;
  }

  // Hide "State Conformity" for federal forms
  const visibleTabs = form.jurisdiction.toLowerCase() === "federal"
    ? TABS.filter((t) => t.key !== "conformity")
    : TABS;

  return (
    <div className="flex flex-col h-full">
      <TopBar form={form} onStatusChange={handleStatusChange} onExport={handleExport} />

      {/* Tab Bar */}
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

      {/* Tab Content */}
      <div className="flex-1 overflow-auto p-6">
        {activeTab === "overview" && <OverviewTab form={form} onUpdate={fetchForm} />}
        {activeTab === "facts" && <FactsTab formId={form.id} />}
        {activeTab === "rules" && <RulesTab formId={form.id} />}
        {activeTab === "lines" && <LineMapTab formId={form.id} />}
        {activeTab === "diagnostics" && <DiagnosticsTab formId={form.id} />}
        {activeTab === "tests" && <TestsTab formId={form.id} />}
        {activeTab === "sources" && <PlaceholderTab name="Sources" />}
        {activeTab === "conformity" && <PlaceholderTab name="State Conformity" />}
      </div>
    </div>
  );
}
