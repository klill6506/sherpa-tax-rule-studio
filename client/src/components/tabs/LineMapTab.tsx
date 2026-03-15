import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import type { FormFact, FormLine, FormRule, PaginatedResponse } from "../../types";

const LINE_TYPES = ["input", "calculated", "subtotal", "total", "informational"] as const;

const LINE_TYPE_BADGES: Record<string, string> = {
  input: "bg-blue-100 text-blue-700",
  calculated: "bg-green-100 text-green-700",
  subtotal: "bg-yellow-100 text-yellow-800",
  total: "bg-gray-800 text-white font-bold",
  informational: "bg-gray-100 text-gray-500",
};

const EMPTY_LINE = {
  line_number: "",
  description: "",
  line_type: "input" as FormLine["line_type"],
  calculation: "",
  source_facts: [] as string[],
  source_rules: [] as string[],
  destination_form: null as string | null,
  notes: "",
  sort_order: 0,
};

interface LineMapTabProps {
  formId: string;
}

export default function LineMapTab({ formId }: LineMapTabProps) {
  const [lines, setLines] = useState<FormLine[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editData, setEditData] = useState<Partial<FormLine>>({});
  const [showAdd, setShowAdd] = useState(false);
  const [newLine, setNewLine] = useState({ ...EMPTY_LINE });
  const [saving, setSaving] = useState(false);
  // Available facts and rules for autocomplete hints
  const [factKeys, setFactKeys] = useState<string[]>([]);
  const [ruleIds, setRuleIds] = useState<string[]>([]);

  const fetchLines = useCallback(async () => {
    try {
      const data = await api.get<PaginatedResponse<FormLine>>(`/forms/${formId}/lines/`);
      setLines(data.results);
    } catch (err) {
      console.error("Failed to fetch lines:", err);
    } finally {
      setLoading(false);
    }
  }, [formId]);

  // Fetch available fact keys and rule IDs for reference
  useEffect(() => {
    void (async () => {
      try {
        const [factsData, rulesData] = await Promise.all([
          api.get<PaginatedResponse<FormFact>>(`/forms/${formId}/facts/`),
          api.get<PaginatedResponse<FormRule>>(`/forms/${formId}/rules/`),
        ]);
        setFactKeys(factsData.results.map((f) => f.fact_key));
        setRuleIds(rulesData.results.map((r) => r.rule_id));
      } catch { /* ignore — autocomplete is a nice-to-have */ }
    })();
  }, [formId]);

  useEffect(() => {
    void fetchLines();
  }, [fetchLines]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const maxSort = lines.length > 0 ? Math.max(...lines.map((l) => l.sort_order)) : 0;
      await api.post(`/forms/${formId}/lines/`, {
        ...newLine,
        tax_form: formId,
        sort_order: newLine.sort_order || maxSort + 10,
        destination_form: newLine.destination_form || null,
      });
      setNewLine({ ...EMPTY_LINE });
      setShowAdd(false);
      await fetchLines();
    } catch (err) {
      console.error("Failed to add line:", err);
    } finally {
      setSaving(false);
    }
  }

  function startEdit(line: FormLine) {
    setEditingId(line.id);
    setEditData({
      line_number: line.line_number,
      description: line.description,
      line_type: line.line_type,
      calculation: line.calculation,
      source_facts: line.source_facts,
      source_rules: line.source_rules,
      destination_form: line.destination_form,
      notes: line.notes,
      sort_order: line.sort_order,
    });
  }

  async function handleSaveEdit() {
    if (!editingId) return;
    setSaving(true);
    try {
      await api.patch(`/forms/${formId}/lines/${editingId}/`, {
        ...editData,
        destination_form: editData.destination_form || null,
      });
      setEditingId(null);
      await fetchLines();
    } catch (err) {
      console.error("Failed to update line:", err);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(lineId: string) {
    if (!confirm("Delete this line?")) return;
    try {
      await api.delete(`/forms/${formId}/lines/${lineId}/`);
      await fetchLines();
    } catch (err) {
      console.error("Failed to delete line:", err);
    }
  }

  function safeJsonParse(str: string, fallback: unknown): unknown {
    try { return JSON.parse(str); }
    catch { return fallback; }
  }

  const inputClass = "w-full rounded border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none";
  const cellClass = "px-3 py-2 text-sm";

  if (loading) return <div className="text-gray-400 text-sm">Loading line map...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">Line Map ({lines.length} lines)</h2>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          + Add Line
        </button>
      </div>

      {/* Autocomplete hints */}
      {(factKeys.length > 0 || ruleIds.length > 0) && (
        <div className="mb-3 text-xs text-gray-400">
          {factKeys.length > 0 && <span>Available facts: {factKeys.join(", ")}</span>}
          {factKeys.length > 0 && ruleIds.length > 0 && <span className="mx-2">|</span>}
          {ruleIds.length > 0 && <span>Available rules: {ruleIds.join(", ")}</span>}
        </div>
      )}

      {/* Add Form */}
      {showAdd && (
        <form onSubmit={handleAdd} className="mb-4 rounded border border-blue-200 bg-blue-50 p-4 space-y-3">
          <div className="grid grid-cols-4 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Line #</label>
              <input type="text" value={newLine.line_number} onChange={(e) => setNewLine({ ...newLine, line_number: e.target.value })} className={inputClass} placeholder="1, 2a, 10" required />
            </div>
            <div className="col-span-2">
              <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
              <input type="text" value={newLine.description} onChange={(e) => setNewLine({ ...newLine, description: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Line Type</label>
              <select value={newLine.line_type} onChange={(e) => setNewLine({ ...newLine, line_type: e.target.value as FormLine["line_type"] })} className={inputClass}>
                {LINE_TYPES.map((lt) => <option key={lt} value={lt}>{lt}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Calculation</label>
              <input type="text" value={newLine.calculation} onChange={(e) => setNewLine({ ...newLine, calculation: e.target.value })} className={inputClass} placeholder="e.g., Line 2 - Line 3" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Flows To</label>
              <input type="text" value={newLine.destination_form ?? ""} onChange={(e) => setNewLine({ ...newLine, destination_form: e.target.value || null })} className={inputClass} placeholder="e.g., 1120S Page 1 Line 4" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Source Facts (JSON array)</label>
              <input
                type="text"
                value={JSON.stringify(newLine.source_facts)}
                onChange={(e) => setNewLine({ ...newLine, source_facts: safeJsonParse(e.target.value, newLine.source_facts) as string[] })}
                className={`${inputClass} font-mono`} placeholder='["sale_price"]'
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Source Rules (JSON array)</label>
              <input
                type="text"
                value={JSON.stringify(newLine.source_rules)}
                onChange={(e) => setNewLine({ ...newLine, source_rules: safeJsonParse(e.target.value, newLine.source_rules) as string[] })}
                className={`${inputClass} font-mono`} placeholder='["R001"]'
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" disabled={saving} className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:opacity-50">
              {saving ? "Adding..." : "Add Line"}
            </button>
            <button type="button" onClick={() => setShowAdd(false)} className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-100">Cancel</button>
          </div>
        </form>
      )}

      {/* Line Map Table */}
      {lines.length === 0 ? (
        <div className="rounded border border-gray-200 bg-white p-8 text-center text-gray-400 text-sm">
          No lines defined yet. Click "Add Line" to map the first form line.
        </div>
      ) : (
        <div className="overflow-x-auto rounded border border-gray-200">
          <table className="w-full bg-white">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className={`${cellClass} text-left font-medium text-gray-600 w-20`}>Line #</th>
                <th className={`${cellClass} text-left font-medium text-gray-600`}>Description</th>
                <th className={`${cellClass} text-center font-medium text-gray-600 w-28`}>Type</th>
                <th className={`${cellClass} text-left font-medium text-gray-600`}>Calculation</th>
                <th className={`${cellClass} text-left font-medium text-gray-600 w-36`}>Source Facts</th>
                <th className={`${cellClass} text-left font-medium text-gray-600 w-28`}>Source Rules</th>
                <th className={`${cellClass} text-left font-medium text-gray-600`}>Flows To</th>
                <th className={`${cellClass} text-right font-medium text-gray-600 w-28`}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {lines.map((line) => {
                const isEditing = editingId === line.id;
                const hasRules = line.source_rules.length > 0;
                const hasDestination = !!line.destination_form;

                return (
                  <tr key={line.id} className={`border-b border-gray-100 ${line.line_type === "total" ? "bg-gray-50 font-semibold" : "hover:bg-gray-50"}`}>
                    {isEditing ? (
                      <>
                        <td className={cellClass}><input type="text" value={editData.line_number ?? ""} onChange={(e) => setEditData({ ...editData, line_number: e.target.value })} className={inputClass} /></td>
                        <td className={cellClass}><input type="text" value={editData.description ?? ""} onChange={(e) => setEditData({ ...editData, description: e.target.value })} className={inputClass} /></td>
                        <td className={cellClass}>
                          <select value={editData.line_type ?? "input"} onChange={(e) => setEditData({ ...editData, line_type: e.target.value as FormLine["line_type"] })} className={inputClass}>
                            {LINE_TYPES.map((lt) => <option key={lt} value={lt}>{lt}</option>)}
                          </select>
                        </td>
                        <td className={cellClass}><input type="text" value={editData.calculation ?? ""} onChange={(e) => setEditData({ ...editData, calculation: e.target.value })} className={inputClass} /></td>
                        <td className={cellClass}>
                          <input
                            type="text"
                            value={JSON.stringify(editData.source_facts ?? [])}
                            onChange={(e) => setEditData({ ...editData, source_facts: safeJsonParse(e.target.value, editData.source_facts) as string[] })}
                            className={`${inputClass} font-mono text-xs`}
                          />
                        </td>
                        <td className={cellClass}>
                          <input
                            type="text"
                            value={JSON.stringify(editData.source_rules ?? [])}
                            onChange={(e) => setEditData({ ...editData, source_rules: safeJsonParse(e.target.value, editData.source_rules) as string[] })}
                            className={`${inputClass} font-mono text-xs`}
                          />
                        </td>
                        <td className={cellClass}><input type="text" value={editData.destination_form ?? ""} onChange={(e) => setEditData({ ...editData, destination_form: e.target.value || null })} className={inputClass} /></td>
                        <td className={`${cellClass} text-right`}>
                          <button onClick={() => void handleSaveEdit()} disabled={saving} className="text-blue-600 hover:text-blue-800 text-xs font-medium mr-2">Save</button>
                          <button onClick={() => setEditingId(null)} className="text-gray-400 hover:text-gray-600 text-xs">Cancel</button>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className={`${cellClass} font-mono font-bold`}>{line.line_number}</td>
                        <td className={cellClass}>{line.description}</td>
                        <td className={`${cellClass} text-center`}>
                          <span className={`rounded px-1.5 py-0.5 text-xs ${LINE_TYPE_BADGES[line.line_type] ?? ""}`}>
                            {line.line_type}
                          </span>
                        </td>
                        <td className={`${cellClass} text-gray-600 text-xs`}>{line.calculation || "—"}</td>
                        <td className={cellClass}>
                          {line.source_facts.length > 0 ? (
                            <div className="flex flex-wrap gap-0.5">
                              {line.source_facts.map((f) => (
                                <span key={f} className="rounded bg-blue-50 px-1 py-0.5 text-xs font-mono text-blue-600">{f}</span>
                              ))}
                            </div>
                          ) : <span className="text-gray-300 text-xs">—</span>}
                        </td>
                        <td className={cellClass}>
                          {line.source_rules.length > 0 ? (
                            <div className="flex items-center gap-1">
                              {hasRules && <span className="text-purple-400 text-xs" title="Driven by rules">⚙</span>}
                              {line.source_rules.map((r) => (
                                <span key={r} className="rounded bg-purple-50 px-1 py-0.5 text-xs font-mono text-purple-600">{r}</span>
                              ))}
                            </div>
                          ) : <span className="text-gray-300 text-xs">—</span>}
                        </td>
                        <td className={cellClass}>
                          {hasDestination ? (
                            <span className="text-xs text-gray-600">
                              <span className="text-emerald-500 mr-1" title="Flows to another form">→</span>
                              {line.destination_form}
                            </span>
                          ) : <span className="text-gray-300 text-xs">—</span>}
                        </td>
                        <td className={`${cellClass} text-right`}>
                          <button onClick={() => startEdit(line)} className="text-blue-600 hover:text-blue-800 text-xs font-medium mr-2">Edit</button>
                          <button onClick={() => handleDelete(line.id)} className="text-red-500 hover:text-red-700 text-xs">Delete</button>
                        </td>
                      </>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
