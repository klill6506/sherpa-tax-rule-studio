import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import type {
  AuthoritySource,
  FormRule,
  PaginatedResponse,
  RuleAuthorityLink,
} from "../../types";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const RULE_TYPES = ["calculation", "classification", "routing", "validation", "conditional"] as const;

const TYPE_COLORS: Record<string, string> = {
  calculation: "bg-blue-50 border-blue-200",
  classification: "bg-green-50 border-green-200",
  routing: "bg-purple-50 border-purple-200",
  validation: "bg-orange-50 border-orange-200",
  conditional: "bg-gray-50 border-gray-200",
};

const TYPE_BADGES: Record<string, string> = {
  calculation: "bg-blue-100 text-blue-800",
  classification: "bg-green-100 text-green-800",
  routing: "bg-purple-100 text-purple-800",
  validation: "bg-orange-100 text-orange-800",
  conditional: "bg-gray-200 text-gray-700",
};

const SUPPORT_LEVELS = ["primary", "secondary", "interpretive", "implementation"] as const;

const SUPPORT_BADGES: Record<string, string> = {
  primary: "bg-red-100 text-red-700",
  secondary: "bg-blue-100 text-blue-700",
  interpretive: "bg-yellow-100 text-yellow-800",
  implementation: "bg-cyan-100 text-cyan-800",
};

const EMPTY_RULE = {
  rule_id: "",
  title: "",
  description: "",
  rule_type: "calculation" as FormRule["rule_type"],
  conditions: {},
  formula: "",
  inputs: [] as string[],
  outputs: [] as string[],
  precedence: 0,
  exceptions: "",
  notes: "",
  sort_order: 0,
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function AuthorityLinksSection({ ruleId, formId }: { ruleId: string; formId: string }) {
  const [links, setLinks] = useState<RuleAuthorityLink[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);

  const fetchLinks = useCallback(async () => {
    try {
      const data = await api.get<PaginatedResponse<RuleAuthorityLink>>(
        `/rule-links/?rule_id=${ruleId}`
      );
      setLinks(data.results);
    } catch (err) {
      console.error("Failed to fetch authority links:", err);
    } finally {
      setLoading(false);
    }
  }, [ruleId]);

  useEffect(() => {
    void fetchLinks();
  }, [fetchLinks]);

  async function handleRemove(linkId: string) {
    if (!confirm("Remove this authority link?")) return;
    try {
      await api.delete(`/rule-links/${linkId}/`);
      await fetchLinks();
    } catch (err) {
      console.error("Failed to remove link:", err);
    }
  }

  if (loading) return <div className="text-xs text-gray-400">Loading authorities...</div>;

  return (
    <div className="mt-4 border-t border-gray-200 pt-3">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-gray-700">Linked Authorities</h4>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="text-xs text-blue-600 hover:text-blue-800 font-medium"
        >
          + Add Authority
        </button>
      </div>

      {links.length === 0 && !showAdd && (
        <p className="text-xs text-gray-400 italic">No authorities linked. Click "Add Authority" to cite a source.</p>
      )}

      {links.map((link) => (
        <div key={link.id} className="flex items-start justify-between rounded bg-white border border-gray-100 px-3 py-2 mb-1.5">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-800 truncate">{link.source_title ?? link.authority_source}</span>
              <span className={`rounded px-1.5 py-0.5 text-xs ${SUPPORT_BADGES[link.support_level] ?? ""}`}>
                {link.support_level}
              </span>
            </div>
            {link.excerpt_label && (
              <p className="text-xs text-purple-600 mt-0.5">{link.excerpt_label}</p>
            )}
            {link.relevance_note && (
              <p className="text-xs text-gray-500 mt-0.5">{link.relevance_note}</p>
            )}
          </div>
          <button
            onClick={() => handleRemove(link.id)}
            className="text-xs text-red-400 hover:text-red-600 ml-2 shrink-0"
          >
            Remove
          </button>
        </div>
      ))}

      {showAdd && (
        <AddAuthorityPanel
          ruleId={ruleId}
          formId={formId}
          onAdded={() => { setShowAdd(false); void fetchLinks(); }}
          onCancel={() => setShowAdd(false)}
        />
      )}
    </div>
  );
}

function AddAuthorityPanel({
  ruleId,
  formId: _formId,
  onAdded,
  onCancel,
}: {
  ruleId: string;
  formId: string;
  onAdded: () => void;
  onCancel: () => void;
}) {
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<AuthoritySource[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedSource, setSelectedSource] = useState<AuthoritySource | null>(null);
  const [supportLevel, setSupportLevel] = useState<RuleAuthorityLink["support_level"]>("primary");
  const [relevanceNote, setRelevanceNote] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSearch() {
    if (!search.trim()) return;
    setSearching(true);
    try {
      const data = await api.get<PaginatedResponse<AuthoritySource>>(`/sources/?q=${encodeURIComponent(search)}`);
      setResults(data.results);
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setSearching(false);
    }
  }

  async function handleSave() {
    if (!selectedSource) return;
    setSaving(true);
    try {
      await api.post("/rule-links/", {
        form_rule: ruleId,
        authority_source: selectedSource.id,
        support_level: supportLevel,
        relevance_note: relevanceNote || null,
      });
      onAdded();
    } catch (err) {
      console.error("Failed to add link:", err);
    } finally {
      setSaving(false);
    }
  }

  const inputClass = "w-full rounded border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none";

  return (
    <div className="rounded border border-blue-200 bg-blue-50 p-3 mt-2 space-y-2">
      {/* Search */}
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Search sources by title, citation, or code..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") void handleSearch(); }}
          className={`${inputClass} flex-1`}
        />
        <button
          onClick={() => void handleSearch()}
          disabled={searching}
          className="rounded bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {searching ? "..." : "Search"}
        </button>
      </div>

      {/* Results */}
      {results.length > 0 && !selectedSource && (
        <div className="max-h-40 overflow-y-auto rounded border border-gray-200 bg-white">
          {results.map((source) => (
            <button
              key={source.id}
              onClick={() => setSelectedSource(source)}
              className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 border-b border-gray-100 last:border-0"
            >
              <span className="font-mono text-xs text-gray-500">{source.source_code}</span>
              <span className="ml-2 text-gray-700">{source.title}</span>
            </button>
          ))}
        </div>
      )}

      {/* Selected source + save */}
      {selectedSource && (
        <div className="space-y-2">
          <div className="rounded bg-white border border-gray-200 px-3 py-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{selectedSource.source_code}: {selectedSource.title}</span>
              <button onClick={() => setSelectedSource(null)} className="text-xs text-gray-400 hover:text-gray-600">Change</button>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-0.5">Support Level</label>
              <select value={supportLevel} onChange={(e) => setSupportLevel(e.target.value as RuleAuthorityLink["support_level"])} className={inputClass}>
                {SUPPORT_LEVELS.map((sl) => <option key={sl} value={sl}>{sl}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-0.5">Relevance Note</label>
              <input type="text" value={relevanceNote} onChange={(e) => setRelevanceNote(e.target.value)} className={inputClass} placeholder="Optional" />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => void handleSave()} disabled={saving} className="rounded bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50">
              {saving ? "Saving..." : "Link Authority"}
            </button>
            <button onClick={onCancel} className="rounded border border-gray-300 px-3 py-1 text-xs hover:bg-gray-100">Cancel</button>
          </div>
        </div>
      )}

      {/* No results */}
      {results.length === 0 && search && !searching && !selectedSource && (
        <p className="text-xs text-gray-400">No sources found. Try a different search term.</p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

interface RulesTabProps {
  formId: string;
}

export default function RulesTab({ formId }: RulesTabProps) {
  const [rules, setRules] = useState<FormRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editData, setEditData] = useState<Partial<FormRule>>({});
  const [showCreate, setShowCreate] = useState(false);
  const [newRule, setNewRule] = useState({ ...EMPTY_RULE });
  const [saving, setSaving] = useState(false);
  const [sortBy, setSortBy] = useState<"precedence" | "rule_id">("precedence");

  const fetchRules = useCallback(async () => {
    try {
      const data = await api.get<PaginatedResponse<FormRule>>(`/forms/${formId}/rules/`);
      setRules(data.results);
    } catch (err) {
      console.error("Failed to fetch rules:", err);
    } finally {
      setLoading(false);
    }
  }, [formId]);

  useEffect(() => {
    void fetchRules();
  }, [fetchRules]);

  const sortedRules = [...rules].sort((a, b) =>
    sortBy === "precedence" ? a.precedence - b.precedence : a.rule_id.localeCompare(b.rule_id)
  );

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post(`/forms/${formId}/rules/`, { ...newRule, tax_form: formId });
      setNewRule({ ...EMPTY_RULE });
      setShowCreate(false);
      await fetchRules();
    } catch (err) {
      console.error("Failed to create rule:", err);
    } finally {
      setSaving(false);
    }
  }

  function startEdit(rule: FormRule) {
    setEditingId(rule.id);
    setEditData({
      rule_id: rule.rule_id,
      title: rule.title,
      description: rule.description,
      rule_type: rule.rule_type,
      conditions: rule.conditions,
      formula: rule.formula,
      inputs: rule.inputs,
      outputs: rule.outputs,
      precedence: rule.precedence,
      exceptions: rule.exceptions,
      notes: rule.notes,
    });
    setExpandedId(rule.id);
  }

  async function handleSaveEdit() {
    if (!editingId) return;
    setSaving(true);
    try {
      await api.patch(`/forms/${formId}/rules/${editingId}/`, editData);
      setEditingId(null);
      await fetchRules();
    } catch (err) {
      console.error("Failed to update rule:", err);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(ruleId: string) {
    if (!confirm("Delete this rule?")) return;
    try {
      await api.delete(`/forms/${formId}/rules/${ruleId}/`);
      if (expandedId === ruleId) setExpandedId(null);
      await fetchRules();
    } catch (err) {
      console.error("Failed to delete rule:", err);
    }
  }

  function safeJsonParse(str: string, fallback: unknown): unknown {
    try { return JSON.parse(str); }
    catch { return fallback; }
  }

  const inputClass = "w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none";

  if (loading) return <div className="text-gray-400 text-sm">Loading rules...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">Rules ({rules.length})</h2>
        <div className="flex items-center gap-3">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as "precedence" | "rule_id")}
            className="rounded border border-gray-300 px-2 py-1 text-xs"
          >
            <option value="precedence">Sort by Precedence</option>
            <option value="rule_id">Sort by Rule ID</option>
          </select>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
          >
            + Add Rule
          </button>
        </div>
      </div>

      {/* Create Form */}
      {showCreate && (
        <form onSubmit={handleCreate} className="mb-4 rounded border border-blue-200 bg-blue-50 p-4 space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Rule ID</label>
              <input type="text" value={newRule.rule_id} onChange={(e) => setNewRule({ ...newRule, rule_id: e.target.value })} className={inputClass} placeholder="R001" required />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Title</label>
              <input type="text" value={newRule.title} onChange={(e) => setNewRule({ ...newRule, title: e.target.value })} className={inputClass} placeholder="Determine gain type" required />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Rule Type</label>
              <select value={newRule.rule_type} onChange={(e) => setNewRule({ ...newRule, rule_type: e.target.value as FormRule["rule_type"] })} className={inputClass}>
                {RULE_TYPES.map((rt) => <option key={rt} value={rt}>{rt}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
            <textarea value={newRule.description} onChange={(e) => setNewRule({ ...newRule, description: e.target.value })} className={`${inputClass} min-h-[60px]`} rows={2} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Precedence</label>
              <input type="number" value={newRule.precedence} onChange={(e) => setNewRule({ ...newRule, precedence: Number(e.target.value) })} className={inputClass} />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Sort Order</label>
              <input type="number" value={newRule.sort_order} onChange={(e) => setNewRule({ ...newRule, sort_order: Number(e.target.value) })} className={inputClass} />
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" disabled={saving} className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:opacity-50">
              {saving ? "Creating..." : "Create Rule"}
            </button>
            <button type="button" onClick={() => setShowCreate(false)} className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-100">Cancel</button>
          </div>
        </form>
      )}

      {/* Rule Cards */}
      {sortedRules.length === 0 ? (
        <div className="rounded border border-gray-200 bg-white p-8 text-center text-gray-400 text-sm">
          No rules defined yet. Click "Add Rule" to create the first one.
        </div>
      ) : (
        <div className="space-y-2">
          {sortedRules.map((rule) => {
            const isExpanded = expandedId === rule.id;
            const isEditing = editingId === rule.id;
            const typeColor = TYPE_COLORS[rule.rule_type] ?? "bg-gray-50 border-gray-200";
            const linkCount = rule.authority_link_count ?? 0;

            return (
              <div key={rule.id} className={`rounded border ${typeColor} transition-all`}>
                {/* Card Header (always visible) */}
                <div
                  className="flex items-center justify-between px-4 py-3 cursor-pointer"
                  onClick={() => setExpandedId(isExpanded ? null : rule.id)}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-400">{isExpanded ? "▼" : "▶"}</span>
                    <span className="font-mono text-sm font-bold text-gray-700">{rule.rule_id}</span>
                    <span className="text-sm text-gray-800">{rule.title}</span>
                    <span className={`rounded px-1.5 py-0.5 text-xs ${TYPE_BADGES[rule.rule_type] ?? ""}`}>
                      {rule.rule_type}
                    </span>
                    {linkCount === 0 ? (
                      <span className="rounded bg-amber-100 text-amber-700 px-1.5 py-0.5 text-xs font-medium">
                        ⚠ No authority
                      </span>
                    ) : (
                      <span className="rounded bg-green-100 text-green-700 px-1.5 py-0.5 text-xs">
                        {linkCount} source{linkCount !== 1 ? "s" : ""}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                    <span className="text-xs text-gray-400">P{rule.precedence}</span>
                    <button onClick={() => startEdit(rule)} className="text-xs text-blue-600 hover:text-blue-800 font-medium">Edit</button>
                    <button onClick={() => handleDelete(rule.id)} className="text-xs text-red-500 hover:text-red-700">Delete</button>
                  </div>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="px-4 pb-4 border-t border-gray-200/50">
                    {isEditing ? (
                      /* Edit Mode */
                      <div className="pt-3 space-y-3">
                        <div className="grid grid-cols-3 gap-3">
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Rule ID</label>
                            <input type="text" value={editData.rule_id ?? ""} onChange={(e) => setEditData({ ...editData, rule_id: e.target.value })} className={inputClass} />
                          </div>
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Title</label>
                            <input type="text" value={editData.title ?? ""} onChange={(e) => setEditData({ ...editData, title: e.target.value })} className={inputClass} />
                          </div>
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Rule Type</label>
                            <select value={editData.rule_type ?? "calculation"} onChange={(e) => setEditData({ ...editData, rule_type: e.target.value as FormRule["rule_type"] })} className={inputClass}>
                              {RULE_TYPES.map((rt) => <option key={rt} value={rt}>{rt}</option>)}
                            </select>
                          </div>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
                          <textarea value={editData.description ?? ""} onChange={(e) => setEditData({ ...editData, description: e.target.value })} className={`${inputClass} min-h-[60px]`} rows={2} />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Formula</label>
                          <textarea value={editData.formula ?? ""} onChange={(e) => setEditData({ ...editData, formula: e.target.value })} className={`${inputClass} font-mono min-h-[60px]`} rows={2} placeholder="e.g., sale_price - adjusted_basis" />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Inputs (JSON array)</label>
                            <textarea
                              value={JSON.stringify(editData.inputs ?? [], null, 2)}
                              onChange={(e) => setEditData({ ...editData, inputs: safeJsonParse(e.target.value, editData.inputs) as string[] })}
                              className={`${inputClass} font-mono min-h-[60px]`} rows={2}
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Outputs (JSON array)</label>
                            <textarea
                              value={JSON.stringify(editData.outputs ?? [], null, 2)}
                              onChange={(e) => setEditData({ ...editData, outputs: safeJsonParse(e.target.value, editData.outputs) as string[] })}
                              className={`${inputClass} font-mono min-h-[60px]`} rows={2}
                            />
                          </div>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Conditions (JSON)</label>
                          <textarea
                            value={JSON.stringify(editData.conditions ?? {}, null, 2)}
                            onChange={(e) => setEditData({ ...editData, conditions: safeJsonParse(e.target.value, editData.conditions) as Record<string, unknown> })}
                            className={`${inputClass} font-mono min-h-[60px]`} rows={2}
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Precedence</label>
                            <input type="number" value={editData.precedence ?? 0} onChange={(e) => setEditData({ ...editData, precedence: Number(e.target.value) })} className={inputClass} />
                          </div>
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Exceptions</label>
                            <input type="text" value={editData.exceptions ?? ""} onChange={(e) => setEditData({ ...editData, exceptions: e.target.value })} className={inputClass} />
                          </div>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
                          <textarea value={editData.notes ?? ""} onChange={(e) => setEditData({ ...editData, notes: e.target.value })} className={inputClass} rows={2} />
                        </div>
                        <div className="flex gap-2 pt-1">
                          <button onClick={() => void handleSaveEdit()} disabled={saving} className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:opacity-50">
                            {saving ? "Saving..." : "Save Changes"}
                          </button>
                          <button onClick={() => setEditingId(null)} className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-100">Cancel</button>
                        </div>

                        <AuthorityLinksSection ruleId={rule.id} formId={formId} />
                      </div>
                    ) : (
                      /* Read Mode */
                      <div className="pt-3 space-y-2 text-sm">
                        {rule.description && (
                          <div>
                            <span className="text-xs font-medium text-gray-500">Description</span>
                            <p className="text-gray-700">{rule.description}</p>
                          </div>
                        )}
                        {rule.formula && (
                          <div>
                            <span className="text-xs font-medium text-gray-500">Formula</span>
                            <p className="font-mono text-gray-700 bg-white/60 rounded px-2 py-1">{rule.formula}</p>
                          </div>
                        )}
                        <div className="grid grid-cols-2 gap-3">
                          {rule.inputs.length > 0 && (
                            <div>
                              <span className="text-xs font-medium text-gray-500">Inputs</span>
                              <div className="flex flex-wrap gap-1 mt-0.5">
                                {rule.inputs.map((inp) => (
                                  <span key={inp} className="rounded bg-white/80 px-1.5 py-0.5 text-xs font-mono text-gray-600">{inp}</span>
                                ))}
                              </div>
                            </div>
                          )}
                          {rule.outputs.length > 0 && (
                            <div>
                              <span className="text-xs font-medium text-gray-500">Outputs</span>
                              <div className="flex flex-wrap gap-1 mt-0.5">
                                {rule.outputs.map((out) => (
                                  <span key={out} className="rounded bg-white/80 px-1.5 py-0.5 text-xs font-mono text-gray-600">{out}</span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                        {Object.keys(rule.conditions).length > 0 && (
                          <div>
                            <span className="text-xs font-medium text-gray-500">Conditions</span>
                            <pre className="font-mono text-xs text-gray-600 bg-white/60 rounded px-2 py-1 overflow-x-auto">{JSON.stringify(rule.conditions, null, 2)}</pre>
                          </div>
                        )}
                        {rule.exceptions && (
                          <div>
                            <span className="text-xs font-medium text-gray-500">Exceptions</span>
                            <p className="text-gray-600">{rule.exceptions}</p>
                          </div>
                        )}
                        {rule.notes && (
                          <div>
                            <span className="text-xs font-medium text-gray-500">Notes</span>
                            <p className="text-gray-600">{rule.notes}</p>
                          </div>
                        )}

                        <AuthorityLinksSection ruleId={rule.id} formId={formId} />
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
