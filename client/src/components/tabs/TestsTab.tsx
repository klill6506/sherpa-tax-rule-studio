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

interface TestResult {
  scenario_id: string;
  scenario_name: string;
  scenario_type?: string;
  passed: boolean;
  values?: Record<string, unknown>;
  errors: Array<{ rule_id: string; error: string }>;
  mismatches: Record<string, { expected: unknown; actual: unknown }>;
}

interface RunAllResult {
  summary: { total: number; passed: number; failed: number };
  results: TestResult[];
}

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

  // Test runner state
  const [runningId, setRunningId] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Map<string, TestResult>>(new Map());
  const [runAllResult, setRunAllResult] = useState<RunAllResult | null>(null);
  const [runningAll, setRunningAll] = useState(false);

  // Quick test state
  const [quickInputs, setQuickInputs] = useState("{}");
  const [quickResult, setQuickResult] = useState<{ values: Record<string, unknown>; errors: Array<{ rule_id: string; error: string }> } | null>(null);
  const [runningQuick, setRunningQuick] = useState(false);

  const fetchScenarios = useCallback(async () => {
    try {
      const data = await api.get<PaginatedResponse<TestScenario>>(`/forms/${formId}/tests/`);
      setScenarios(data.results);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, [formId]);

  useEffect(() => { void fetchScenarios(); }, [fetchScenarios]);

  function safeJsonParse(str: string, fallback: unknown): unknown {
    try { return JSON.parse(str); } catch { return fallback; }
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault(); setSaving(true);
    try {
      await api.post(`/forms/${formId}/tests/`, { ...newScenario, tax_form: formId });
      setNewScenario({ ...EMPTY_SCENARIO }); setShowAdd(false); await fetchScenarios();
    } catch (err) { console.error(err); } finally { setSaving(false); }
  }

  function startEdit(s: TestScenario) {
    setEditingId(s.id); setExpandedId(s.id);
    setEditData({ scenario_name: s.scenario_name, scenario_type: s.scenario_type, inputs: s.inputs, expected_outputs: s.expected_outputs, notes: s.notes });
  }

  async function handleSaveEdit() {
    if (!editingId) return; setSaving(true);
    try { await api.patch(`/forms/${formId}/tests/${editingId}/`, editData); setEditingId(null); await fetchScenarios(); }
    catch (err) { console.error(err); } finally { setSaving(false); }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this test scenario?")) return;
    try { await api.delete(`/forms/${formId}/tests/${id}/`); if (expandedId === id) setExpandedId(null); await fetchScenarios(); }
    catch (err) { console.error(err); }
  }

  // --- Test Runner ---
  async function runSingle(scenarioId: string) {
    setRunningId(scenarioId);
    try {
      const result = await api.post<TestResult>(`/forms/${formId}/run_test/`, { scenario_id: scenarioId });
      setTestResults(prev => new Map(prev).set(scenarioId, result));
      setExpandedId(scenarioId);
    } catch (err) { console.error(err); }
    finally { setRunningId(null); }
  }

  async function runAll() {
    setRunningAll(true); setRunAllResult(null); setTestResults(new Map());
    try {
      const result = await api.post<RunAllResult>(`/forms/${formId}/run_test/`, { run_all: true });
      setRunAllResult(result);
      const map = new Map<string, TestResult>();
      for (const r of result.results) { map.set(r.scenario_id, r); }
      setTestResults(map);
    } catch (err) { console.error(err); }
    finally { setRunningAll(false); }
  }

  async function runQuickTest() {
    setRunningQuick(true); setQuickResult(null);
    try {
      const inputs = JSON.parse(quickInputs);
      const result = await api.post<{ passed: boolean; values: Record<string, unknown>; errors: Array<{ rule_id: string; error: string }> }>(
        `/forms/${formId}/run_test/`, { inputs }
      );
      setQuickResult(result);
    } catch (err) { console.error(err); }
    finally { setRunningQuick(false); }
  }

  const inputClass = "w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none";

  if (loading) return <div className="text-gray-400 text-sm">Loading test scenarios...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">Test Scenarios ({scenarios.length})</h2>
        <div className="flex gap-2">
          <button
            onClick={() => void runAll()}
            disabled={runningAll || scenarios.length === 0}
            className="rounded bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50 transition-colors"
          >
            {runningAll ? "Running..." : "Run All Tests"}
          </button>
          <button onClick={() => setShowAdd(!showAdd)} className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors">
            + Add Scenario
          </button>
        </div>
      </div>

      {/* Run All Summary */}
      {runAllResult && (
        <div className={`rounded border px-4 py-3 mb-4 ${runAllResult.summary.failed === 0 ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"}`}>
          <span className="text-sm font-medium">
            Test Results: <span className="text-green-700">{runAllResult.summary.passed} passed</span>
            {runAllResult.summary.failed > 0 && <>, <span className="text-red-700">{runAllResult.summary.failed} failed</span></>}
            <span className="text-gray-500"> of {runAllResult.summary.total}</span>
          </span>
        </div>
      )}

      {/* Add Form */}
      {showAdd && (
        <form onSubmit={handleAdd} className="mb-4 rounded border border-blue-200 bg-blue-50 p-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="block text-xs font-medium text-gray-600 mb-1">Scenario Name</label><input type="text" value={newScenario.scenario_name} onChange={e => setNewScenario({...newScenario, scenario_name: e.target.value})} className={inputClass} required /></div>
            <div><label className="block text-xs font-medium text-gray-600 mb-1">Type</label><select value={newScenario.scenario_type} onChange={e => setNewScenario({...newScenario, scenario_type: e.target.value as TestScenario["scenario_type"]})} className={inputClass}>{SCENARIO_TYPES.map(st => <option key={st} value={st}>{st}</option>)}</select></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="block text-xs font-medium text-gray-600 mb-1">Inputs (JSON)</label><textarea value={JSON.stringify(newScenario.inputs, null, 2)} onChange={e => setNewScenario({...newScenario, inputs: safeJsonParse(e.target.value, newScenario.inputs) as Record<string, unknown>})} className={`${inputClass} font-mono min-h-[80px]`} rows={3} /></div>
            <div><label className="block text-xs font-medium text-gray-600 mb-1">Expected Outputs (JSON)</label><textarea value={JSON.stringify(newScenario.expected_outputs, null, 2)} onChange={e => setNewScenario({...newScenario, expected_outputs: safeJsonParse(e.target.value, newScenario.expected_outputs) as Record<string, unknown>})} className={`${inputClass} font-mono min-h-[80px]`} rows={3} /></div>
          </div>
          <div className="flex gap-2">
            <button type="submit" disabled={saving} className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:opacity-50">{saving ? "Adding..." : "Add Scenario"}</button>
            <button type="button" onClick={() => setShowAdd(false)} className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-100">Cancel</button>
          </div>
        </form>
      )}

      {/* Scenario List */}
      {scenarios.length === 0 && !showAdd ? (
        <div className="rounded border border-gray-200 bg-white p-8 text-center text-gray-400 text-sm">No test scenarios yet.</div>
      ) : (
        <div className="space-y-2">
          {scenarios.map(scenario => {
            const isExpanded = expandedId === scenario.id;
            const isEditing = editingId === scenario.id;
            const result = testResults.get(scenario.id);
            const isRunning = runningId === scenario.id;

            return (
              <div key={scenario.id} className={`rounded border bg-white ${result ? (result.passed ? "border-green-300" : "border-red-300") : "border-gray-200"}`}>
                <div className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-50" onClick={() => setExpandedId(isExpanded ? null : scenario.id)}>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-400">{isExpanded ? "▼" : "▶"}</span>
                    {result && (
                      <span className={`text-sm font-bold ${result.passed ? "text-green-600" : "text-red-600"}`}>
                        {result.passed ? "PASS" : "FAIL"}
                      </span>
                    )}
                    <span className="text-sm font-medium text-gray-800">{scenario.scenario_name}</span>
                    <span className={`rounded px-1.5 py-0.5 text-xs ${SCENARIO_BADGES[scenario.scenario_type] ?? ""}`}>{scenario.scenario_type}</span>
                  </div>
                  <div className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
                    <button onClick={() => void runSingle(scenario.id)} disabled={isRunning} className="rounded bg-emerald-600 px-2.5 py-1 text-xs text-white hover:bg-emerald-700 disabled:opacity-50">
                      {isRunning ? "Running..." : "Run"}
                    </button>
                    <button onClick={() => startEdit(scenario)} className="text-xs text-blue-600 hover:text-blue-800 font-medium">Edit</button>
                    <button onClick={() => handleDelete(scenario.id)} className="text-xs text-red-500 hover:text-red-700">Delete</button>
                  </div>
                </div>

                {isExpanded && (
                  <div className="px-4 pb-4 border-t border-gray-100">
                    {/* Test Result */}
                    {result && (
                      <div className={`rounded p-3 mt-2 mb-3 text-sm ${result.passed ? "bg-green-50" : "bg-red-50"}`}>
                        {Object.keys(result.mismatches).length > 0 && (
                          <div className="space-y-1">
                            {Object.entries(result.mismatches).map(([key, mm]) => (
                              <div key={key}>
                                <span className="text-gray-600">Expected:</span> <span className="font-mono">{key} = {JSON.stringify(mm.expected)}</span><br />
                                <span className="text-gray-600">Got:</span> <span className="font-mono text-red-600">{key} = {JSON.stringify(mm.actual)}</span> <span className="text-red-500 text-xs font-bold">MISMATCH</span>
                              </div>
                            ))}
                          </div>
                        )}
                        {result.errors.length > 0 && (
                          <div className="mt-2 space-y-1">
                            {result.errors.map((err, i) => (
                              <div key={i} className="text-amber-700">Rule {err.rule_id}: {err.error}</div>
                            ))}
                          </div>
                        )}
                        {result.passed && Object.keys(result.mismatches).length === 0 && result.errors.length === 0 && (
                          <div className="text-green-700 font-medium">All expected outputs match.</div>
                        )}
                      </div>
                    )}

                    {isEditing ? (
                      <div className="pt-2 space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <div><label className="block text-xs font-medium text-gray-600 mb-1">Scenario Name</label><input type="text" value={editData.scenario_name ?? ""} onChange={e => setEditData({...editData, scenario_name: e.target.value})} className={inputClass} /></div>
                          <div><label className="block text-xs font-medium text-gray-600 mb-1">Type</label><select value={editData.scenario_type ?? "normal"} onChange={e => setEditData({...editData, scenario_type: e.target.value as TestScenario["scenario_type"]})} className={inputClass}>{SCENARIO_TYPES.map(st => <option key={st} value={st}>{st}</option>)}</select></div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div><label className="block text-xs font-medium text-gray-600 mb-1">Inputs (JSON)</label><textarea value={JSON.stringify(editData.inputs ?? {}, null, 2)} onChange={e => setEditData({...editData, inputs: safeJsonParse(e.target.value, editData.inputs) as Record<string, unknown>})} className={`${inputClass} font-mono min-h-[100px]`} rows={4} /></div>
                          <div><label className="block text-xs font-medium text-gray-600 mb-1">Expected Outputs (JSON)</label><textarea value={JSON.stringify(editData.expected_outputs ?? {}, null, 2)} onChange={e => setEditData({...editData, expected_outputs: safeJsonParse(e.target.value, editData.expected_outputs) as Record<string, unknown>})} className={`${inputClass} font-mono min-h-[100px]`} rows={4} /></div>
                        </div>
                        <div className="flex gap-2"><button onClick={() => void handleSaveEdit()} disabled={saving} className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:opacity-50">{saving ? "Saving..." : "Save"}</button><button onClick={() => setEditingId(null)} className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-100">Cancel</button></div>
                      </div>
                    ) : (
                      <div className="pt-2 grid grid-cols-2 gap-4">
                        <div>
                          <span className="text-xs font-medium text-gray-500">Inputs</span>
                          <pre className="font-mono text-xs text-gray-600 bg-gray-50 rounded px-2 py-1.5 mt-1 overflow-x-auto">{JSON.stringify(scenario.inputs, null, 2)}</pre>
                        </div>
                        <div>
                          <span className="text-xs font-medium text-gray-500">Expected Outputs</span>
                          <pre className="font-mono text-xs text-gray-600 bg-gray-50 rounded px-2 py-1.5 mt-1 overflow-x-auto">{JSON.stringify(scenario.expected_outputs, null, 2)}</pre>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Quick Test Panel */}
      <div className="mt-6 rounded border border-gray-200 bg-white p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Quick Test</h3>
        <p className="text-xs text-gray-400 mb-2">Enter inputs as JSON and run against this form's rules without saving a scenario.</p>
        <div className="flex gap-3">
          <textarea
            value={quickInputs}
            onChange={e => setQuickInputs(e.target.value)}
            className={`${inputClass} font-mono flex-1 min-h-[80px]`}
            rows={3}
            placeholder='{"sale_price": 100000, "adjusted_basis": 60000}'
          />
          <div className="flex flex-col gap-2">
            <button
              onClick={() => void runQuickTest()}
              disabled={runningQuick}
              className="rounded bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              {runningQuick ? "Running..." : "Run"}
            </button>
          </div>
        </div>
        {quickResult && (
          <div className="mt-3 rounded bg-gray-50 p-3">
            <span className="text-xs font-medium text-gray-500">Computed Values:</span>
            <pre className="font-mono text-xs text-gray-700 mt-1 overflow-x-auto">{JSON.stringify(quickResult.values, null, 2)}</pre>
            {quickResult.errors.length > 0 && (
              <div className="mt-2">
                <span className="text-xs font-medium text-amber-600">Errors:</span>
                {quickResult.errors.map((err, i) => (
                  <div key={i} className="text-xs text-amber-700 mt-0.5">Rule {err.rule_id}: {err.error}</div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
