import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import type { FormDiagnostic, PaginatedResponse } from "../../types";

const SEVERITIES = ["error", "warning", "info"] as const;

const SEVERITY_BADGES: Record<string, string> = {
  error: "bg-red-100 text-red-700",
  warning: "bg-yellow-100 text-yellow-800",
  info: "bg-blue-100 text-blue-700",
};

const EMPTY_DIAG = {
  diagnostic_id: "",
  title: "",
  severity: "warning" as FormDiagnostic["severity"],
  condition: "",
  message: "",
  notes: "",
};

interface DiagnosticsTabProps {
  formId: string;
}

export default function DiagnosticsTab({ formId }: DiagnosticsTabProps) {
  const [diagnostics, setDiagnostics] = useState<FormDiagnostic[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editData, setEditData] = useState<Partial<FormDiagnostic>>({});
  const [showAdd, setShowAdd] = useState(false);
  const [newDiag, setNewDiag] = useState({ ...EMPTY_DIAG });
  const [saving, setSaving] = useState(false);

  const fetchDiagnostics = useCallback(async () => {
    try {
      const data = await api.get<PaginatedResponse<FormDiagnostic>>(`/forms/${formId}/diagnostics/`);
      setDiagnostics(data.results);
    } catch (err) {
      console.error("Failed to fetch diagnostics:", err);
    } finally {
      setLoading(false);
    }
  }, [formId]);

  useEffect(() => {
    void fetchDiagnostics();
  }, [fetchDiagnostics]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post(`/forms/${formId}/diagnostics/`, { ...newDiag, tax_form: formId });
      setNewDiag({ ...EMPTY_DIAG });
      setShowAdd(false);
      await fetchDiagnostics();
    } catch (err) {
      console.error("Failed to add diagnostic:", err);
    } finally {
      setSaving(false);
    }
  }

  function startEdit(diag: FormDiagnostic) {
    setEditingId(diag.id);
    setEditData({
      diagnostic_id: diag.diagnostic_id,
      title: diag.title,
      severity: diag.severity,
      condition: diag.condition,
      message: diag.message,
      notes: diag.notes,
    });
  }

  async function handleSaveEdit() {
    if (!editingId) return;
    setSaving(true);
    try {
      await api.patch(`/forms/${formId}/diagnostics/${editingId}/`, editData);
      setEditingId(null);
      await fetchDiagnostics();
    } catch (err) {
      console.error("Failed to update diagnostic:", err);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(diagId: string) {
    if (!confirm("Delete this diagnostic?")) return;
    try {
      await api.delete(`/forms/${formId}/diagnostics/${diagId}/`);
      await fetchDiagnostics();
    } catch (err) {
      console.error("Failed to delete diagnostic:", err);
    }
  }

  const inputClass = "w-full rounded border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none";
  const cellClass = "px-3 py-2 text-sm";

  if (loading) return <div className="text-gray-400 text-sm">Loading diagnostics...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">Diagnostics ({diagnostics.length})</h2>
        <button onClick={() => setShowAdd(!showAdd)} className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors">
          + Add Diagnostic
        </button>
      </div>

      {showAdd && (
        <form onSubmit={handleAdd} className="mb-4 rounded border border-blue-200 bg-blue-50 p-4 space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Diagnostic ID</label>
              <input type="text" value={newDiag.diagnostic_id} onChange={(e) => setNewDiag({ ...newDiag, diagnostic_id: e.target.value })} className={inputClass} placeholder="D001" required />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Title</label>
              <input type="text" value={newDiag.title} onChange={(e) => setNewDiag({ ...newDiag, title: e.target.value })} className={inputClass} required />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Severity</label>
              <select value={newDiag.severity} onChange={(e) => setNewDiag({ ...newDiag, severity: e.target.value as FormDiagnostic["severity"] })} className={inputClass}>
                {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Condition (when this fires)</label>
            <textarea value={newDiag.condition} onChange={(e) => setNewDiag({ ...newDiag, condition: e.target.value })} className={inputClass} rows={2} />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Message (shown to preparer)</label>
            <textarea value={newDiag.message} onChange={(e) => setNewDiag({ ...newDiag, message: e.target.value })} className={inputClass} rows={2} />
          </div>
          <div className="flex gap-2">
            <button type="submit" disabled={saving} className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:opacity-50">{saving ? "Adding..." : "Add Diagnostic"}</button>
            <button type="button" onClick={() => setShowAdd(false)} className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-100">Cancel</button>
          </div>
        </form>
      )}

      {diagnostics.length === 0 ? (
        <div className="rounded border border-gray-200 bg-white p-8 text-center text-gray-400 text-sm">
          No diagnostics defined yet.
        </div>
      ) : (
        <div className="overflow-x-auto rounded border border-gray-200">
          <table className="w-full bg-white">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className={`${cellClass} text-left font-medium text-gray-600 w-20`}>ID</th>
                <th className={`${cellClass} text-left font-medium text-gray-600`}>Title</th>
                <th className={`${cellClass} text-center font-medium text-gray-600 w-24`}>Severity</th>
                <th className={`${cellClass} text-left font-medium text-gray-600`}>Condition</th>
                <th className={`${cellClass} text-left font-medium text-gray-600`}>Message</th>
                <th className={`${cellClass} text-right font-medium text-gray-600 w-28`}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {diagnostics.map((diag) => {
                const isEditing = editingId === diag.id;
                return (
                  <tr key={diag.id} className="border-b border-gray-100 hover:bg-gray-50">
                    {isEditing ? (
                      <>
                        <td className={cellClass}><input type="text" value={editData.diagnostic_id ?? ""} onChange={(e) => setEditData({ ...editData, diagnostic_id: e.target.value })} className={inputClass} /></td>
                        <td className={cellClass}><input type="text" value={editData.title ?? ""} onChange={(e) => setEditData({ ...editData, title: e.target.value })} className={inputClass} /></td>
                        <td className={cellClass}>
                          <select value={editData.severity ?? "warning"} onChange={(e) => setEditData({ ...editData, severity: e.target.value as FormDiagnostic["severity"] })} className={inputClass}>
                            {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
                          </select>
                        </td>
                        <td className={cellClass}><input type="text" value={editData.condition ?? ""} onChange={(e) => setEditData({ ...editData, condition: e.target.value })} className={inputClass} /></td>
                        <td className={cellClass}><input type="text" value={editData.message ?? ""} onChange={(e) => setEditData({ ...editData, message: e.target.value })} className={inputClass} /></td>
                        <td className={`${cellClass} text-right`}>
                          <button onClick={() => void handleSaveEdit()} disabled={saving} className="text-blue-600 hover:text-blue-800 text-xs font-medium mr-2">Save</button>
                          <button onClick={() => setEditingId(null)} className="text-gray-400 hover:text-gray-600 text-xs">Cancel</button>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className={`${cellClass} font-mono text-xs font-bold`}>{diag.diagnostic_id}</td>
                        <td className={cellClass}>{diag.title}</td>
                        <td className={`${cellClass} text-center`}>
                          <span className={`rounded px-1.5 py-0.5 text-xs ${SEVERITY_BADGES[diag.severity] ?? ""}`}>{diag.severity}</span>
                        </td>
                        <td className={`${cellClass} text-xs text-gray-600`}>{diag.condition || "—"}</td>
                        <td className={`${cellClass} text-xs text-gray-600`}>{diag.message || "—"}</td>
                        <td className={`${cellClass} text-right`}>
                          <button onClick={() => startEdit(diag)} className="text-blue-600 hover:text-blue-800 text-xs font-medium mr-2">Edit</button>
                          <button onClick={() => handleDelete(diag.id)} className="text-red-500 hover:text-red-700 text-xs">Delete</button>
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
