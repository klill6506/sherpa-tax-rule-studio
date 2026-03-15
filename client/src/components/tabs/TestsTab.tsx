import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import type { PaginatedResponse, TestScenario } from "../../types";

const SCENARIO_TYPES = ["normal", "edge", "failure"] as const;

const SCENARIO_BADGES: Record<string, string> = {
  normal: "bg-green-100 text-green-700",
  edge: "bg-yellow-100 text-yellow-800",
  failure: "bg-red-100 text-red-700",
};

const EMPTY_SCENARIO = {
  scenario_name: "",
  scenario_type: "normal" as TestScenario["scenario_type"],
  inputs: {} as Record<string, unknown>,
  expected_outputs: {} as Record<string, unknown>,
  notes: "",
  sort_order: 0,
};

interface TestsTabProps {
  formId: string;
}

export default function TestsTab({ formId }: TestsTabProps) {
  const [scenarios, setScenarios] = useState<TestScenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editData, setEditData] = useState<Partial<TestScenario>>({});
  const [showAdd, setShowAdd] = useState(false);
  const [newScenario, setNewScenario] = useState({ ...EMPTY_SCENARIO });
  const [saving, setSaving] = useState(false);

  const fetchScenarios = useCallback(async () => {
    try {
      const data = await api.get<PaginatedResponse<TestScenario>>(`/forms/${formId}/tests/`);
      setScenarios(data.results);
    } catch (err) {
      console.error("Failed to fetch test scenarios:", err);
    } finally {
      setLoading(false);
    }
  }, [formId]);

  useEffect(() => {
    void fetchScenarios();
  }, [fetchScenarios]);

  function safeJsonParse(str: string, fallback: unknown): unknown {
    try { return JSON.parse(str); }
    catch { return fallback; }
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post(`/forms/${formId}/tests/`, { ...newScenario, tax_form: formId });
      setNewScenario({ ...EMPTY_SCENARIO });
      setShowAdd(false);
      await fetchScenarios();
    } catch (err) {
      console.error("Failed to add scenario:", err);
    } finally {
      setSaving(false);
    }
  }

  function startEdit(scenario: TestScenario) {
    setEditingId(scenario.id);
    setEditData({
      scenario_name: scenario.scenario_name,
      scenario_type: scenario.scenario_type,
      inputs: scenario.inputs,
      expected_outputs: scenario.expected_outputs,
      notes: scenario.notes,
    });
    setExpandedId(scenario.id);
  }

  async function handleSaveEdit() {
    if (!editingId) return;
    setSaving(true);
    try {
      await api.patch(`/forms/${formId}/tests/${editingId}/`, editData);
      setEditingId(null);
      await fetchScenarios();
    } catch (err) {
      console.error("Failed to update scenario:", err);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(scenarioId: string) {
    if (!confirm("Delete this test scenario?")) return;
    try {
      await api.delete(`/forms/${formId}/tests/${scenarioId}/`);
      if (expandedId === scenarioId) setExpandedId(null);
      await fetchScenarios();
    } catch (err) {
      console.error("Failed to delete scenario:", err);
    }
  }

  const inputClass = "w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none";

  if (loading) return <div className="text-gray-400 text-sm">Loading test scenarios...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">Test Scenarios ({scenarios.length})</h2>
        <div className="flex gap-2">
          <button disabled className="rounded border border-gray-300 px-3 py-1.5 text-sm text-gray-400 cursor-not-allowed" title="Test runner coming in a future session">
            Run Tests
          </button>
          <button onClick={() => setShowAdd(!showAdd)} className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors">
            + Add Scenario
          </button>
        </div>
      </div>

      {showAdd && (
        <form onSubmit={handleAdd} className="mb-4 rounded border border-blue-200 bg-blue-50 p-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Scenario Name</label>
              <input type="text" value={newScenario.scenario_name} onChange={(e) => setNewScenario({ ...newScenario, scenario_name: e.target.value })} className={inputClass} placeholder="Basic 1231 gain, held > 1 year" required />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
              <select value={newScenario.scenario_type} onChange={(e) => setNewScenario({ ...newScenario, scenario_type: e.target.value as TestScenario["scenario_type"] })} className={inputClass}>
                {SCENARIO_TYPES.map((st) => <option key={st} value={st}>{st}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Inputs (JSON)</label>
              <textarea
                value={JSON.stringify(newScenario.inputs, null, 2)}
                onChange={(e) => setNewScenario({ ...newScenario, inputs: safeJsonParse(e.target.value, newScenario.inputs) as Record<string, unknown> })}
                className={`${inputClass} font-mono min-h-[80px]`} rows={3} placeholder='{"sale_price": 100000, "adjusted_basis": 50000}'
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Expected Outputs (JSON)</label>
              <textarea
                value={JSON.stringify(newScenario.expected_outputs, null, 2)}
                onChange={(e) => setNewScenario({ ...newScenario, expected_outputs: safeJsonParse(e.target.value, newScenario.expected_outputs) as Record<string, unknown> })}
                className={`${inputClass} font-mono min-h-[80px]`} rows={3} placeholder='{"line_10": 50000, "gain_type": "1231"}'
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
            <input type="text" value={newScenario.notes} onChange={(e) => setNewScenario({ ...newScenario, notes: e.target.value })} className={inputClass} />
          </div>
          <div className="flex gap-2">
            <button type="submit" disabled={saving} className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:opacity-50">{saving ? "Adding..." : "Add Scenario"}</button>
            <button type="button" onClick={() => setShowAdd(false)} className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-100">Cancel</button>
          </div>
        </form>
      )}

      {scenarios.length === 0 ? (
        <div className="rounded border border-gray-200 bg-white p-8 text-center text-gray-400 text-sm">
          No test scenarios yet. Click "Add Scenario" to define test cases.
        </div>
      ) : (
        <div className="space-y-2">
          {scenarios.map((scenario) => {
            const isExpanded = expandedId === scenario.id;
            const isEditing = editingId === scenario.id;

            return (
              <div key={scenario.id} className="rounded border border-gray-200 bg-white">
                {/* Header */}
                <div
                  className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-50"
                  onClick={() => setExpandedId(isExpanded ? null : scenario.id)}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-400">{isExpanded ? "▼" : "▶"}</span>
                    <span className="text-sm font-medium text-gray-800">{scenario.scenario_name}</span>
                    <span className={`rounded px-1.5 py-0.5 text-xs ${SCENARIO_BADGES[scenario.scenario_type] ?? ""}`}>
                      {scenario.scenario_type}
                    </span>
                  </div>
                  <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                    <button onClick={() => startEdit(scenario)} className="text-xs text-blue-600 hover:text-blue-800 font-medium">Edit</button>
                    <button onClick={() => handleDelete(scenario.id)} className="text-xs text-red-500 hover:text-red-700">Delete</button>
                  </div>
                </div>

                {/* Expanded */}
                {isExpanded && (
                  <div className="px-4 pb-4 border-t border-gray-100">
                    {isEditing ? (
                      <div className="pt-3 space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Scenario Name</label>
                            <input type="text" value={editData.scenario_name ?? ""} onChange={(e) => setEditData({ ...editData, scenario_name: e.target.value })} className={inputClass} />
                          </div>
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
                            <select value={editData.scenario_type ?? "normal"} onChange={(e) => setEditData({ ...editData, scenario_type: e.target.value as TestScenario["scenario_type"] })} className={inputClass}>
                              {SCENARIO_TYPES.map((st) => <option key={st} value={st}>{st}</option>)}
                            </select>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Inputs (JSON)</label>
                            <textarea
                              value={JSON.stringify(editData.inputs ?? {}, null, 2)}
                              onChange={(e) => setEditData({ ...editData, inputs: safeJsonParse(e.target.value, editData.inputs) as Record<string, unknown> })}
                              className={`${inputClass} font-mono min-h-[100px]`} rows={4}
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Expected Outputs (JSON)</label>
                            <textarea
                              value={JSON.stringify(editData.expected_outputs ?? {}, null, 2)}
                              onChange={(e) => setEditData({ ...editData, expected_outputs: safeJsonParse(e.target.value, editData.expected_outputs) as Record<string, unknown> })}
                              className={`${inputClass} font-mono min-h-[100px]`} rows={4}
                            />
                          </div>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
                          <input type="text" value={editData.notes ?? ""} onChange={(e) => setEditData({ ...editData, notes: e.target.value })} className={inputClass} />
                        </div>
                        <div className="flex gap-2">
                          <button onClick={() => void handleSaveEdit()} disabled={saving} className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:opacity-50">{saving ? "Saving..." : "Save Changes"}</button>
                          <button onClick={() => setEditingId(null)} className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-100">Cancel</button>
                        </div>
                      </div>
                    ) : (
                      <div className="pt-3 grid grid-cols-2 gap-4">
                        <div>
                          <span className="text-xs font-medium text-gray-500">Inputs</span>
                          <pre className="font-mono text-xs text-gray-600 bg-gray-50 rounded px-2 py-1.5 mt-1 overflow-x-auto">
                            {JSON.stringify(scenario.inputs, null, 2)}
                          </pre>
                        </div>
                        <div>
                          <span className="text-xs font-medium text-gray-500">Expected Outputs</span>
                          <pre className="font-mono text-xs text-gray-600 bg-gray-50 rounded px-2 py-1.5 mt-1 overflow-x-auto">
                            {JSON.stringify(scenario.expected_outputs, null, 2)}
                          </pre>
                        </div>
                        {scenario.notes && (
                          <div className="col-span-2">
                            <span className="text-xs font-medium text-gray-500">Notes</span>
                            <p className="text-sm text-gray-600">{scenario.notes}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
