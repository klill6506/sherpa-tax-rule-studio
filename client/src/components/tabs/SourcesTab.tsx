import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import type { AuthoritySource, PaginatedResponse } from "../../types";

interface FormLinkRecord {
  id: string;
  authority_source: string;
  form_code: string;
  form_part_code: string | null;
  line_code: string | null;
  link_type: string;
  note: string | null;
  source_code?: string;
  created_at: string;
}

const LINK_TYPE_BADGES: Record<string, string> = {
  governs: "bg-blue-700 text-white",
  informs: "bg-blue-100 text-blue-700",
  validates: "bg-green-100 text-green-700",
  mapping_only: "bg-gray-200 text-gray-600",
  overrides: "bg-red-100 text-red-700",
};
const LINK_TYPE_LABELS: Record<string, string> = {
  governs: "Governing Sources",
  informs: "Informing Sources",
  validates: "Validating Sources",
  mapping_only: "Mapping Sources",
  overrides: "Overriding Sources",
};
const LINK_TYPES = ["governs", "informs", "validates", "mapping_only", "overrides"] as const;

interface SourcesTabProps {
  formId: string;
  formNumber: string;
}

export default function SourcesTab({ formId: _formId, formNumber }: SourcesTabProps) {
  const [links, setLinks] = useState<FormLinkRecord[]>([]);
  const [sourceMap, setSourceMap] = useState<Map<string, AuthoritySource>>(new Map());
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [search, setSearch] = useState("");
  const [searchResults, setSearchResults] = useState<AuthoritySource[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedSource, setSelectedSource] = useState<AuthoritySource | null>(null);
  const [linkType, setLinkType] = useState<string>("governs");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);

  const fetchLinks = useCallback(async () => {
    try {
      const d = await api.get<PaginatedResponse<FormLinkRecord>>(`/form-links/?form_code=${encodeURIComponent(formNumber)}`);
      setLinks(d.results);
      // Fetch source details for each unique source
      const sourceIds = [...new Set(d.results.map(l => l.authority_source))];
      const sources = new Map<string, AuthoritySource>();
      await Promise.all(sourceIds.map(async (sid) => {
        try {
          const s = await api.get<AuthoritySource>(`/sources/${sid}/`);
          sources.set(sid, s);
        } catch { /* ignore */ }
      }));
      setSourceMap(sources);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, [formNumber]);

  useEffect(() => { void fetchLinks(); }, [fetchLinks]);

  async function handleSearch() {
    if (!search.trim()) return;
    setSearching(true);
    try {
      const d = await api.get<PaginatedResponse<AuthoritySource>>(`/sources/?q=${encodeURIComponent(search)}`);
      setSearchResults(d.results);
    } catch (err) { console.error(err); }
    finally { setSearching(false); }
  }

  async function handleAdd() {
    if (!selectedSource) return;
    setSaving(true);
    try {
      await api.post("/form-links/", {
        authority_source: selectedSource.id,
        form_code: formNumber,
        link_type: linkType,
        note: note || null,
      });
      setSelectedSource(null);
      setSearch("");
      setSearchResults([]);
      setNote("");
      setShowAdd(false);
      await fetchLinks();
    } catch (err) { console.error(err); }
    finally { setSaving(false); }
  }

  async function handleRemove(linkId: string) {
    if (!confirm("Remove this source link?")) return;
    try { await api.delete(`/form-links/${linkId}/`); await fetchLinks(); }
    catch (err) { console.error(err); }
  }

  if (loading) return <div className="text-gray-400 text-sm">Loading sources...</div>;

  // Group links by type
  const grouped = new Map<string, FormLinkRecord[]>();
  for (const link of links) {
    if (!grouped.has(link.link_type)) grouped.set(link.link_type, []);
    grouped.get(link.link_type)!.push(link);
  }

  const inputClass = "w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none";

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">Sources for {formNumber} ({links.length})</h2>
        <button onClick={() => setShowAdd(!showAdd)} className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors">
          + Link Source
        </button>
      </div>

      {/* Add Panel */}
      {showAdd && (
        <div className="mb-4 rounded border border-blue-200 bg-blue-50 p-4 space-y-3">
          <div className="flex gap-2">
            <input
              type="text" placeholder="Search sources by title, citation, or code..."
              value={search} onChange={e => setSearch(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter") void handleSearch(); }}
              className={`${inputClass} flex-1`}
            />
            <button onClick={() => void handleSearch()} disabled={searching} className="rounded bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50">
              {searching ? "..." : "Search"}
            </button>
          </div>
          {searchResults.length > 0 && !selectedSource && (
            <div className="max-h-40 overflow-y-auto rounded border border-gray-200 bg-white">
              {searchResults.map(s => (
                <button key={s.id} onClick={() => setSelectedSource(s)} className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 border-b border-gray-100 last:border-0">
                  <span className="font-mono text-xs text-gray-500">{s.source_code}</span>
                  <span className="ml-2 text-gray-700">{s.title}</span>
                </button>
              ))}
            </div>
          )}
          {selectedSource && (
            <div className="space-y-2">
              <div className="rounded bg-white border border-gray-200 px-3 py-2 flex items-center justify-between">
                <span className="text-sm font-medium">{selectedSource.source_code}: {selectedSource.title}</span>
                <button onClick={() => setSelectedSource(null)} className="text-xs text-gray-400 hover:text-gray-600">Change</button>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-0.5">Link Type</label>
                  <select value={linkType} onChange={e => setLinkType(e.target.value)} className={inputClass}>
                    {LINK_TYPES.map(lt => <option key={lt} value={lt}>{lt}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-0.5">Note</label>
                  <input type="text" value={note} onChange={e => setNote(e.target.value)} className={inputClass} placeholder="Optional" />
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => void handleAdd()} disabled={saving} className="rounded bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50">
                  {saving ? "Linking..." : "Link Source"}
                </button>
                <button onClick={() => setShowAdd(false)} className="rounded border border-gray-300 px-3 py-1 text-xs hover:bg-gray-100">Cancel</button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Grouped source list */}
      {links.length === 0 ? (
        <div className="rounded border border-gray-200 bg-white p-8 text-center text-gray-400 text-sm">
          No sources linked to this form yet. Click "Link Source" to add one.
        </div>
      ) : (
        <div className="space-y-4">
          {LINK_TYPES.filter(lt => grouped.has(lt)).map(lt => (
            <div key={lt}>
              <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <span className={`rounded px-1.5 py-0.5 text-xs ${LINK_TYPE_BADGES[lt] ?? ""}`}>{lt}</span>
                {LINK_TYPE_LABELS[lt]}
              </h3>
              <div className="space-y-1">
                {grouped.get(lt)!.map(link => {
                  const source = sourceMap.get(link.authority_source);
                  return (
                    <div key={link.id} className="flex items-center justify-between rounded border border-gray-200 bg-white px-4 py-2.5">
                      <div className="flex-1 min-w-0">
                        <Link to={`/sources/${link.authority_source}`} className="text-sm font-medium text-blue-600 hover:text-blue-800">
                          {source?.source_code ?? link.authority_source}
                        </Link>
                        {source && <span className="text-sm text-gray-600 ml-2">{source.title}</span>}
                        {source?.citation && <span className="text-xs text-gray-400 ml-2">{source.citation}</span>}
                        {link.note && <p className="text-xs text-gray-500 mt-0.5">{link.note}</p>}
                      </div>
                      <div className="flex items-center gap-3 ml-4 shrink-0">
                        {source && <span className="text-xs text-gray-400">{source.jurisdiction_code}</span>}
                        <button onClick={() => handleRemove(link.id)} className="text-xs text-red-500 hover:text-red-700">Remove</button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
