import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import type { FormFact, PaginatedResponse } from "../../types";

const DATA_TYPES = ["string", "integer", "decimal", "boolean", "date", "choice"] as const;

const EMPTY_FACT: Omit<FormFact, "id" | "tax_form" | "created_at" | "updated_at"> = {
  fact_key: "",
  label: "",
  data_type: "string",
  required: false,
  default_value: null,
  validation_rule: null,
  choices: null,
  sort_order: 0,
  notes: "",
};

interface FactsTabProps {
  formId: string;
}

export default function FactsTab({ formId }: FactsTabProps) {
  const [facts, setFacts] = useState<FormFact[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editData, setEditData] = useState<Partial<FormFact>>({});
  const [showAdd, setShowAdd] = useState(false);
  const [newFact, setNewFact] = useState({ ...EMPTY_FACT });
  const [saving, setSaving] = useState(false);

  const fetchFacts = useCallback(async () => {
    try {
      const data = await api.get<PaginatedResponse<FormFact>>(`/forms/${formId}/facts/`);
      setFacts(data.results);
    } catch (err) {
      console.error("Failed to fetch facts:", err);
    } finally {
      setLoading(false);
    }
  }, [formId]);

  useEffect(() => {
    void fetchFacts();
  }, [fetchFacts]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post(`/forms/${formId}/facts/`, { ...newFact, tax_form: formId });
      setNewFact({ ...EMPTY_FACT });
      setShowAdd(false);
      await fetchFacts();
    } catch (err) {
      console.error("Failed to add fact:", err);
    } finally {
      setSaving(false);
    }
  }

  function startEdit(fact: FormFact) {
    setEditingId(fact.id);
    setEditData({
      fact_key: fact.fact_key,
      label: fact.label,
      data_type: fact.data_type,
      required: fact.required,
      default_value: fact.default_value,
      validation_rule: fact.validation_rule,
      sort_order: fact.sort_order,
      notes: fact.notes,
    });
  }

  async function handleSaveEdit() {
    if (!editingId) return;
    setSaving(true);
    try {
      await api.patch(`/forms/${formId}/facts/${editingId}/`, editData);
      setEditingId(null);
      await fetchFacts();
    } catch (err) {
      console.error("Failed to update fact:", err);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(factId: string) {
    if (!confirm("Delete this fact?")) return;
    try {
      await api.delete(`/forms/${formId}/facts/${factId}/`);
      await fetchFacts();
    } catch (err) {
      console.error("Failed to delete fact:", err);
    }
  }

  const cellClass = "px-3 py-2 text-sm";
  const inputClass =
    "w-full rounded border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none";

  if (loading) {
    return <div className="text-gray-400 text-sm">Loading facts...</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">
          Facts ({facts.length})
        </h2>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          + Add Fact
        </button>
      </div>

      {/* Add Form */}
      {showAdd && (
        <form onSubmit={handleAdd} className="mb-4 rounded border border-blue-200 bg-blue-50 p-4">
          <div className="grid grid-cols-4 gap-3 mb-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Fact Key</label>
              <input
                type="text"
                value={newFact.fact_key}
                onChange={(e) => setNewFact({ ...newFact, fact_key: e.target.value })}
                className={inputClass}
                placeholder="sale_price"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Label</label>
              <input
                type="text"
                value={newFact.label}
                onChange={(e) => setNewFact({ ...newFact, label: e.target.value })}
                className={inputClass}
                placeholder="Sale Price"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Data Type</label>
              <select
                value={newFact.data_type}
                onChange={(e) => setNewFact({ ...newFact, data_type: e.target.value as FormFact["data_type"] })}
                className={inputClass}
              >
                {DATA_TYPES.map((dt) => (
                  <option key={dt} value={dt}>{dt}</option>
                ))}
              </select>
            </div>
            <div className="flex items-end gap-3">
              <label className="flex items-center gap-1.5 text-sm pb-1">
                <input
                  type="checkbox"
                  checked={newFact.required}
                  onChange={(e) => setNewFact({ ...newFact, required: e.target.checked })}
                  className="rounded border-gray-300"
                />
                Required
              </label>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3 mb-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Default Value</label>
              <input
                type="text"
                value={newFact.default_value ?? ""}
                onChange={(e) => setNewFact({ ...newFact, default_value: e.target.value || null })}
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Validation Rule</label>
              <input
                type="text"
                value={newFact.validation_rule ?? ""}
                onChange={(e) => setNewFact({ ...newFact, validation_rule: e.target.value || null })}
                className={inputClass}
                placeholder="must be >= 0"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Sort Order</label>
              <input
                type="number"
                value={newFact.sort_order}
                onChange={(e) => setNewFact({ ...newFact, sort_order: Number(e.target.value) })}
                className={inputClass}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={saving}
              className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? "Adding..." : "Add Fact"}
            </button>
            <button
              type="button"
              onClick={() => setShowAdd(false)}
              className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-100"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Facts Table */}
      {facts.length === 0 ? (
        <div className="rounded border border-gray-200 bg-white p-8 text-center text-gray-400 text-sm">
          No facts defined yet. Click "Add Fact" to create the first one.
        </div>
      ) : (
        <div className="overflow-x-auto rounded border border-gray-200">
          <table className="w-full bg-white">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className={`${cellClass} text-left font-medium text-gray-600`}>Key</th>
                <th className={`${cellClass} text-left font-medium text-gray-600`}>Label</th>
                <th className={`${cellClass} text-left font-medium text-gray-600`}>Type</th>
                <th className={`${cellClass} text-center font-medium text-gray-600`}>Req</th>
                <th className={`${cellClass} text-left font-medium text-gray-600`}>Default</th>
                <th className={`${cellClass} text-left font-medium text-gray-600`}>Validation</th>
                <th className={`${cellClass} text-center font-medium text-gray-600`}>Order</th>
                <th className={`${cellClass} text-right font-medium text-gray-600`}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {facts.map((fact) => (
                <tr key={fact.id} className="border-b border-gray-100 hover:bg-gray-50">
                  {editingId === fact.id ? (
                    <>
                      <td className={cellClass}>
                        <input
                          type="text"
                          value={editData.fact_key ?? ""}
                          onChange={(e) => setEditData({ ...editData, fact_key: e.target.value })}
                          className={inputClass}
                        />
                      </td>
                      <td className={cellClass}>
                        <input
                          type="text"
                          value={editData.label ?? ""}
                          onChange={(e) => setEditData({ ...editData, label: e.target.value })}
                          className={inputClass}
                        />
                      </td>
                      <td className={cellClass}>
                        <select
                          value={editData.data_type ?? "string"}
                          onChange={(e) => setEditData({ ...editData, data_type: e.target.value as FormFact["data_type"] })}
                          className={inputClass}
                        >
                          {DATA_TYPES.map((dt) => (
                            <option key={dt} value={dt}>{dt}</option>
                          ))}
                        </select>
                      </td>
                      <td className={`${cellClass} text-center`}>
                        <input
                          type="checkbox"
                          checked={editData.required ?? false}
                          onChange={(e) => setEditData({ ...editData, required: e.target.checked })}
                          className="rounded border-gray-300"
                        />
                      </td>
                      <td className={cellClass}>
                        <input
                          type="text"
                          value={editData.default_value ?? ""}
                          onChange={(e) => setEditData({ ...editData, default_value: e.target.value || null })}
                          className={inputClass}
                        />
                      </td>
                      <td className={cellClass}>
                        <input
                          type="text"
                          value={editData.validation_rule ?? ""}
                          onChange={(e) => setEditData({ ...editData, validation_rule: e.target.value || null })}
                          className={inputClass}
                        />
                      </td>
                      <td className={`${cellClass} text-center`}>
                        <input
                          type="number"
                          value={editData.sort_order ?? 0}
                          onChange={(e) => setEditData({ ...editData, sort_order: Number(e.target.value) })}
                          className={`${inputClass} w-16 text-center`}
                        />
                      </td>
                      <td className={`${cellClass} text-right`}>
                        <button
                          onClick={handleSaveEdit}
                          disabled={saving}
                          className="text-blue-600 hover:text-blue-800 text-xs font-medium mr-2"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => setEditingId(null)}
                          className="text-gray-400 hover:text-gray-600 text-xs"
                        >
                          Cancel
                        </button>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className={`${cellClass} font-mono text-xs`}>{fact.fact_key}</td>
                      <td className={cellClass}>{fact.label}</td>
                      <td className={cellClass}>
                        <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs">{fact.data_type}</span>
                      </td>
                      <td className={`${cellClass} text-center`}>
                        {fact.required && <span className="text-green-600 font-bold">*</span>}
                      </td>
                      <td className={`${cellClass} text-gray-500`}>{fact.default_value ?? "—"}</td>
                      <td className={`${cellClass} text-gray-500 text-xs`}>{fact.validation_rule ?? "—"}</td>
                      <td className={`${cellClass} text-center text-gray-400`}>{fact.sort_order}</td>
                      <td className={`${cellClass} text-right`}>
                        <button
                          onClick={() => startEdit(fact)}
                          className="text-blue-600 hover:text-blue-800 text-xs font-medium mr-2"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(fact.id)}
                          className="text-red-500 hover:text-red-700 text-xs"
                        >
                          Delete
                        </button>
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
