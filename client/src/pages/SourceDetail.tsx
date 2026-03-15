import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import type {
  AuthorityExcerpt,
  AuthoritySource,
  AuthorityTopic,
  AuthorityVersion,
  PaginatedResponse,
} from "../types";

// ---------------------------------------------------------------------------
// Types for form links and source topics (local to this page)
// ---------------------------------------------------------------------------
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
interface SourceTopicRecord {
  id: number;
  authority_source: string;
  authority_topic: string;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const SOURCE_TYPES = [
  "code_section","regulation","official_form","official_instruction","official_publication",
  "official_notice","official_revenue_ruling","official_revenue_procedure","mef_schema",
  "mef_business_rule","mef_release_memo","state_statute","state_regulation","state_form",
  "state_instruction","state_efile_spec","state_vendor_guide","state_conformity_notice",
  "internal_memo","internal_example","internal_test_case",
] as const;
const SOURCE_RANKS = ["controlling","primary_official","implementation_official","internal_interpretation","reference_only"] as const;
const STATUSES = ["active","superseded","draft","archived"] as const;
const LINK_TYPES = ["governs","informs","validates","mapping_only","overrides"] as const;
const LINK_TYPE_BADGES: Record<string, string> = {
  governs: "bg-blue-700 text-white", informs: "bg-blue-100 text-blue-700",
  validates: "bg-green-100 text-green-700", mapping_only: "bg-gray-200 text-gray-600",
  overrides: "bg-red-100 text-red-700",
};
const FILE_TYPES = ["pdf","html","xml","zip","json"] as const;

const inputClass = "w-full rounded border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none";
const labelClass = "block text-xs font-medium text-gray-600 mb-1";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function genSourceCode(jurisdiction: string, sourceType: string, title: string): string {
  const j = (jurisdiction || "FED").toUpperCase();
  const t = sourceType.toUpperCase().replace(/^OFFICIAL_/, "").replace(/^STATE_/, "ST_").slice(0, 10);
  const slug = title.replace(/[^a-zA-Z0-9]+/g, "_").toUpperCase().slice(0, 30);
  return `${j}_${t}_${slug}`.replace(/_+$/, "");
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ExcerptsSection({ sourceId }: { sourceId: string }) {
  const [excerpts, setExcerpts] = useState<AuthorityExcerpt[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editData, setEditData] = useState<Partial<AuthorityExcerpt>>({});
  const [showAdd, setShowAdd] = useState(false);
  const [saving, setSaving] = useState(false);
  const [newExcerpt, setNewExcerpt] = useState({
    excerpt_label: "", location_reference: "", excerpt_text: "", summary_text: "",
    topic_tags: [] as string[], line_or_page_start: "", line_or_page_end: "",
    effective_year_start: null as number | null, effective_year_end: null as number | null,
    is_key_excerpt: false,
  });

  const fetch = useCallback(async () => {
    try {
      const d = await api.get<PaginatedResponse<AuthorityExcerpt>>(`/sources/${sourceId}/excerpts/`);
      setExcerpts(d.results);
    } catch { /* ignore */ } finally { setLoading(false); }
  }, [sourceId]);
  useEffect(() => { void fetch(); }, [fetch]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault(); setSaving(true);
    try {
      await api.post(`/sources/${sourceId}/excerpts/`, { ...newExcerpt, authority_source: sourceId });
      setNewExcerpt({ excerpt_label: "", location_reference: "", excerpt_text: "", summary_text: "", topic_tags: [], line_or_page_start: "", line_or_page_end: "", effective_year_start: null, effective_year_end: null, is_key_excerpt: false });
      setShowAdd(false); await fetch();
    } catch (err) { console.error(err); } finally { setSaving(false); }
  }
  function startEdit(ex: AuthorityExcerpt) {
    setEditingId(ex.id); setExpandedId(ex.id);
    setEditData({ excerpt_label: ex.excerpt_label, location_reference: ex.location_reference, excerpt_text: ex.excerpt_text, summary_text: ex.summary_text, topic_tags: ex.topic_tags, line_or_page_start: ex.line_or_page_start, line_or_page_end: ex.line_or_page_end, effective_year_start: ex.effective_year_start, effective_year_end: ex.effective_year_end, is_key_excerpt: ex.is_key_excerpt });
  }
  async function handleSaveEdit() {
    if (!editingId) return; setSaving(true);
    try { await api.patch(`/sources/${sourceId}/excerpts/${editingId}/`, editData); setEditingId(null); await fetch(); }
    catch (err) { console.error(err); } finally { setSaving(false); }
  }
  async function handleDelete(id: string) {
    if (!confirm("Delete this excerpt?")) return;
    try { await api.delete(`/sources/${sourceId}/excerpts/${id}/`); await fetch(); } catch (err) { console.error(err); }
  }

  if (loading) return <div className="text-xs text-gray-400">Loading excerpts...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-700">Excerpts ({excerpts.length})</h3>
        <button onClick={() => setShowAdd(!showAdd)} className="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Add Excerpt</button>
      </div>
      {showAdd && (
        <form onSubmit={handleAdd} className="mb-3 rounded border border-blue-200 bg-blue-50 p-3 space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <div><label className={labelClass}>Label</label><input type="text" value={newExcerpt.excerpt_label} onChange={e => setNewExcerpt({...newExcerpt, excerpt_label: e.target.value})} className={inputClass} placeholder="Part III overview" /></div>
            <div><label className={labelClass}>Location Ref</label><input type="text" value={newExcerpt.location_reference} onChange={e => setNewExcerpt({...newExcerpt, location_reference: e.target.value})} className={inputClass} placeholder="Page 5, Section 3" /></div>
          </div>
          <div><label className={labelClass}>Excerpt Text</label><textarea value={newExcerpt.excerpt_text} onChange={e => setNewExcerpt({...newExcerpt, excerpt_text: e.target.value})} className={`${inputClass} min-h-[100px]`} rows={4} required /></div>
          <div><label className={labelClass}>Summary</label><textarea value={newExcerpt.summary_text} onChange={e => setNewExcerpt({...newExcerpt, summary_text: e.target.value})} className={inputClass} rows={2} /></div>
          <div className="grid grid-cols-3 gap-2">
            <div><label className={labelClass}>Topic Tags (comma-separated)</label><input type="text" value={newExcerpt.topic_tags.join(", ")} onChange={e => setNewExcerpt({...newExcerpt, topic_tags: e.target.value.split(",").map(t => t.trim()).filter(Boolean)})} className={inputClass} /></div>
            <div><label className={labelClass}>Page/Line Start</label><input type="text" value={newExcerpt.line_or_page_start} onChange={e => setNewExcerpt({...newExcerpt, line_or_page_start: e.target.value})} className={inputClass} /></div>
            <div className="flex items-end gap-2"><label className="flex items-center gap-1.5 text-sm pb-1"><input type="checkbox" checked={newExcerpt.is_key_excerpt} onChange={e => setNewExcerpt({...newExcerpt, is_key_excerpt: e.target.checked})} className="rounded border-gray-300" />Key Excerpt</label></div>
          </div>
          <div className="flex gap-2">
            <button type="submit" disabled={saving} className="rounded bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50">{saving ? "Adding..." : "Add Excerpt"}</button>
            <button type="button" onClick={() => setShowAdd(false)} className="rounded border border-gray-300 px-3 py-1 text-xs hover:bg-gray-100">Cancel</button>
          </div>
        </form>
      )}
      {excerpts.length === 0 && !showAdd && <p className="text-xs text-gray-400 italic">No excerpts. Click "Add Excerpt" to paste source material.</p>}
      <div className="space-y-1.5">
        {excerpts.map(ex => {
          const isExpanded = expandedId === ex.id;
          const isEditing = editingId === ex.id;
          return (
            <div key={ex.id} className="rounded border border-gray-200 bg-white">
              <div className="flex items-center justify-between px-3 py-2 cursor-pointer" onClick={() => setExpandedId(isExpanded ? null : ex.id)}>
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <span className="text-xs text-gray-400">{isExpanded ? "▼" : "▶"}</span>
                  {ex.is_key_excerpt && <span className="text-yellow-500" title="Key excerpt">★</span>}
                  <span className="text-sm font-medium text-gray-700 truncate">{ex.excerpt_label || "Untitled excerpt"}</span>
                  {ex.location_reference && <span className="text-xs text-gray-400">({ex.location_reference})</span>}
                </div>
                <div className="flex gap-2" onClick={e => e.stopPropagation()}>
                  <button onClick={() => startEdit(ex)} className="text-xs text-blue-600 hover:text-blue-800">Edit</button>
                  <button onClick={() => handleDelete(ex.id)} className="text-xs text-red-500 hover:text-red-700">Delete</button>
                </div>
              </div>
              {isExpanded && (
                <div className="px-3 pb-3 border-t border-gray-100">
                  {isEditing ? (
                    <div className="pt-2 space-y-2">
                      <div className="grid grid-cols-2 gap-2">
                        <div><label className={labelClass}>Label</label><input type="text" value={editData.excerpt_label ?? ""} onChange={e => setEditData({...editData, excerpt_label: e.target.value})} className={inputClass} /></div>
                        <div><label className={labelClass}>Location Ref</label><input type="text" value={editData.location_reference ?? ""} onChange={e => setEditData({...editData, location_reference: e.target.value})} className={inputClass} /></div>
                      </div>
                      <div><label className={labelClass}>Excerpt Text</label><textarea value={editData.excerpt_text ?? ""} onChange={e => setEditData({...editData, excerpt_text: e.target.value})} className={`${inputClass} min-h-[100px]`} rows={4} /></div>
                      <div><label className={labelClass}>Summary</label><textarea value={editData.summary_text ?? ""} onChange={e => setEditData({...editData, summary_text: e.target.value})} className={inputClass} rows={2} /></div>
                      <div className="grid grid-cols-3 gap-2">
                        <div><label className={labelClass}>Topic Tags</label><input type="text" value={(editData.topic_tags ?? []).join(", ")} onChange={e => setEditData({...editData, topic_tags: e.target.value.split(",").map(t => t.trim()).filter(Boolean)})} className={inputClass} /></div>
                        <div><label className={labelClass}>Page/Line Start</label><input type="text" value={editData.line_or_page_start ?? ""} onChange={e => setEditData({...editData, line_or_page_start: e.target.value})} className={inputClass} /></div>
                        <div className="flex items-end"><label className="flex items-center gap-1.5 text-sm pb-1"><input type="checkbox" checked={editData.is_key_excerpt ?? false} onChange={e => setEditData({...editData, is_key_excerpt: e.target.checked})} className="rounded border-gray-300" />Key Excerpt</label></div>
                      </div>
                      <div className="flex gap-2"><button onClick={() => void handleSaveEdit()} disabled={saving} className="rounded bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50">Save</button><button onClick={() => setEditingId(null)} className="rounded border border-gray-300 px-3 py-1 text-xs hover:bg-gray-100">Cancel</button></div>
                    </div>
                  ) : (
                    <div className="pt-2">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{ex.excerpt_text}</p>
                      {ex.summary_text && <p className="text-xs text-gray-500 mt-2 italic">{ex.summary_text}</p>}
                      {ex.topic_tags.length > 0 && <div className="flex gap-1 mt-2">{ex.topic_tags.map(t => <span key={t} className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500">{t}</span>)}</div>}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function VersionsSection({ sourceId }: { sourceId: string }) {
  const [versions, setVersions] = useState<AuthorityVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [saving, setSaving] = useState(false);
  const [newVer, setNewVer] = useState({ version_label: "", version_date: "", file_type: "pdf", retrieval_url: "", file_path: "", checksum_sha256: "" });

  const fetch = useCallback(async () => {
    try { const d = await api.get<PaginatedResponse<AuthorityVersion>>(`/sources/${sourceId}/versions/`); setVersions(d.results); }
    catch { /* ignore */ } finally { setLoading(false); }
  }, [sourceId]);
  useEffect(() => { void fetch(); }, [fetch]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault(); setSaving(true);
    try {
      await api.post(`/sources/${sourceId}/versions/`, { ...newVer, authority_source: sourceId, version_date: newVer.version_date || null, retrieval_url: newVer.retrieval_url || null, file_path: newVer.file_path || null, checksum_sha256: newVer.checksum_sha256 || null });
      setNewVer({ version_label: "", version_date: "", file_type: "pdf", retrieval_url: "", file_path: "", checksum_sha256: "" });
      setShowAdd(false); await fetch();
    } catch (err) { console.error(err); } finally { setSaving(false); }
  }
  async function handleMarkCurrent(id: string) {
    try { await api.post(`/sources/${sourceId}/versions/${id}/mark_current/`, {}); await fetch(); }
    catch (err) { console.error(err); }
  }
  async function handleDelete(id: string) {
    if (!confirm("Delete this version?")) return;
    try { await api.delete(`/sources/${sourceId}/versions/${id}/`); await fetch(); } catch (err) { console.error(err); }
  }

  if (loading) return <div className="text-xs text-gray-400">Loading versions...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-700">Versions ({versions.length})</h3>
        <button onClick={() => setShowAdd(!showAdd)} className="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Add Version</button>
      </div>
      {showAdd && (
        <form onSubmit={handleAdd} className="mb-3 rounded border border-blue-200 bg-blue-50 p-3 space-y-2">
          <div className="grid grid-cols-3 gap-2">
            <div><label className={labelClass}>Version Label</label><input type="text" value={newVer.version_label} onChange={e => setNewVer({...newVer, version_label: e.target.value})} className={inputClass} placeholder="TY2025 v3.0" required /></div>
            <div><label className={labelClass}>Date</label><input type="date" value={newVer.version_date} onChange={e => setNewVer({...newVer, version_date: e.target.value})} className={inputClass} /></div>
            <div><label className={labelClass}>File Type</label><select value={newVer.file_type} onChange={e => setNewVer({...newVer, file_type: e.target.value})} className={inputClass}>{FILE_TYPES.map(ft => <option key={ft} value={ft}>{ft}</option>)}</select></div>
          </div>
          <div><label className={labelClass}>Retrieval URL</label><input type="text" value={newVer.retrieval_url} onChange={e => setNewVer({...newVer, retrieval_url: e.target.value})} className={inputClass} /></div>
          <div className="flex gap-2"><button type="submit" disabled={saving} className="rounded bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50">{saving ? "Adding..." : "Add Version"}</button><button type="button" onClick={() => setShowAdd(false)} className="rounded border border-gray-300 px-3 py-1 text-xs hover:bg-gray-100">Cancel</button></div>
        </form>
      )}
      {versions.length === 0 && !showAdd && <p className="text-xs text-gray-400 italic">No versions tracked.</p>}
      {versions.length > 0 && (
        <table className="w-full text-sm">
          <thead><tr className="border-b text-left text-xs text-gray-500"><th className="py-1 pr-3">Label</th><th className="py-1 pr-3">Date</th><th className="py-1 pr-3">Type</th><th className="py-1 pr-3">Current?</th><th className="py-1 text-right">Actions</th></tr></thead>
          <tbody>
            {versions.map(v => (
              <tr key={v.id} className="border-b border-gray-100">
                <td className="py-1.5 pr-3 font-medium">{v.version_label}</td>
                <td className="py-1.5 pr-3 text-gray-500">{v.version_date ?? "—"}</td>
                <td className="py-1.5 pr-3"><span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs">{v.file_type}</span></td>
                <td className="py-1.5 pr-3">{v.is_current ? <span className="rounded bg-green-100 text-green-700 px-1.5 py-0.5 text-xs font-medium">Current</span> : <button onClick={() => handleMarkCurrent(v.id)} className="text-xs text-blue-600 hover:text-blue-800">Mark Current</button>}</td>
                <td className="py-1.5 text-right"><button onClick={() => handleDelete(v.id)} className="text-xs text-red-500 hover:text-red-700">Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function TopicTagsSection({ sourceId }: { sourceId: string }) {
  const [linkedTopics, setLinkedTopics] = useState<SourceTopicRecord[]>([]);
  const [allTopics, setAllTopics] = useState<AuthorityTopic[]>([]);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    try {
      const [stData, topicData] = await Promise.all([
        api.get<PaginatedResponse<SourceTopicRecord>>(`/source-topics/?authority_source=${sourceId}`),
        api.get<PaginatedResponse<AuthorityTopic>>("/topics/?page_size=200"),
      ]);
      setLinkedTopics(stData.results);
      setAllTopics(topicData.results);
    } catch { /* ignore */ } finally { setLoading(false); }
  }, [sourceId]);
  useEffect(() => { void fetch(); }, [fetch]);

  const linkedTopicIds = new Set(linkedTopics.map(lt => lt.authority_topic));
  const availableTopics = allTopics.filter(t => !linkedTopicIds.has(t.id));

  async function handleAdd(topicId: string) {
    try { await api.post("/source-topics/", { authority_source: sourceId, authority_topic: topicId }); await fetch(); }
    catch (err) { console.error(err); }
  }
  async function handleRemove(linkId: number) {
    try { await api.delete(`/source-topics/${linkId}/`); await fetch(); }
    catch (err) { console.error(err); }
  }

  if (loading) return <div className="text-xs text-gray-400">Loading topics...</div>;

  const topicMap = new Map(allTopics.map(t => [t.id, t]));

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Topic Tags</h3>
      <div className="flex flex-wrap gap-1.5 mb-2">
        {linkedTopics.map(lt => {
          const topic = topicMap.get(lt.authority_topic);
          return (
            <span key={lt.id} className="flex items-center gap-1 rounded bg-purple-100 text-purple-700 px-2 py-0.5 text-xs">
              {topic?.topic_name ?? lt.authority_topic}
              <button onClick={() => handleRemove(lt.id)} className="text-purple-400 hover:text-purple-600 ml-0.5">×</button>
            </span>
          );
        })}
        {linkedTopics.length === 0 && <span className="text-xs text-gray-400 italic">No topics tagged.</span>}
      </div>
      {availableTopics.length > 0 && (
        <select onChange={e => { if (e.target.value) { void handleAdd(e.target.value); e.target.value = ""; } }} className="rounded border border-gray-300 px-2 py-1 text-xs" defaultValue="">
          <option value="" disabled>+ Add topic...</option>
          {availableTopics.map(t => <option key={t.id} value={t.id}>{t.topic_name}</option>)}
        </select>
      )}
    </div>
  );
}

function FormLinksSection({ sourceId }: { sourceId: string }) {
  const [links, setLinks] = useState<FormLinkRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [saving, setSaving] = useState(false);
  const [newLink, setNewLink] = useState({ form_code: "", form_part_code: "", line_code: "", link_type: "governs", note: "" });

  const fetch = useCallback(async () => {
    try { const d = await api.get<PaginatedResponse<FormLinkRecord>>(`/form-links/?source_id=${sourceId}`); setLinks(d.results); }
    catch { /* ignore */ } finally { setLoading(false); }
  }, [sourceId]);
  useEffect(() => { void fetch(); }, [fetch]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault(); setSaving(true);
    try {
      await api.post("/form-links/", { authority_source: sourceId, form_code: newLink.form_code, form_part_code: newLink.form_part_code || null, line_code: newLink.line_code || null, link_type: newLink.link_type, note: newLink.note || null });
      setNewLink({ form_code: "", form_part_code: "", line_code: "", link_type: "governs", note: "" });
      setShowAdd(false); await fetch();
    } catch (err) { console.error(err); } finally { setSaving(false); }
  }
  async function handleDelete(id: string) {
    if (!confirm("Remove this form link?")) return;
    try { await api.delete(`/form-links/${id}/`); await fetch(); } catch (err) { console.error(err); }
  }

  if (loading) return <div className="text-xs text-gray-400">Loading form links...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-700">Form Links ({links.length})</h3>
        <button onClick={() => setShowAdd(!showAdd)} className="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Add Form Link</button>
      </div>
      {showAdd && (
        <form onSubmit={handleAdd} className="mb-3 rounded border border-blue-200 bg-blue-50 p-3 space-y-2">
          <div className="grid grid-cols-4 gap-2">
            <div><label className={labelClass}>Form Code</label><input type="text" value={newLink.form_code} onChange={e => setNewLink({...newLink, form_code: e.target.value})} className={inputClass} placeholder="4797" required /></div>
            <div><label className={labelClass}>Part</label><input type="text" value={newLink.form_part_code} onChange={e => setNewLink({...newLink, form_part_code: e.target.value})} className={inputClass} placeholder="Part III" /></div>
            <div><label className={labelClass}>Line</label><input type="text" value={newLink.line_code} onChange={e => setNewLink({...newLink, line_code: e.target.value})} className={inputClass} /></div>
            <div><label className={labelClass}>Link Type</label><select value={newLink.link_type} onChange={e => setNewLink({...newLink, link_type: e.target.value})} className={inputClass}>{LINK_TYPES.map(lt => <option key={lt} value={lt}>{lt}</option>)}</select></div>
          </div>
          <div><label className={labelClass}>Note</label><input type="text" value={newLink.note} onChange={e => setNewLink({...newLink, note: e.target.value})} className={inputClass} /></div>
          <div className="flex gap-2"><button type="submit" disabled={saving} className="rounded bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50">{saving ? "Adding..." : "Add Link"}</button><button type="button" onClick={() => setShowAdd(false)} className="rounded border border-gray-300 px-3 py-1 text-xs hover:bg-gray-100">Cancel</button></div>
        </form>
      )}
      {links.length === 0 && !showAdd && <p className="text-xs text-gray-400 italic">No form links.</p>}
      {links.length > 0 && (
        <table className="w-full text-sm">
          <thead><tr className="border-b text-left text-xs text-gray-500"><th className="py-1 pr-3">Form</th><th className="py-1 pr-3">Part</th><th className="py-1 pr-3">Line</th><th className="py-1 pr-3">Type</th><th className="py-1 pr-3">Note</th><th className="py-1 text-right">Actions</th></tr></thead>
          <tbody>
            {links.map(lk => (
              <tr key={lk.id} className="border-b border-gray-100">
                <td className="py-1.5 pr-3 font-mono font-medium">{lk.form_code}</td>
                <td className="py-1.5 pr-3 text-gray-500">{lk.form_part_code ?? "—"}</td>
                <td className="py-1.5 pr-3 text-gray-500">{lk.line_code ?? "—"}</td>
                <td className="py-1.5 pr-3"><span className={`rounded px-1.5 py-0.5 text-xs ${LINK_TYPE_BADGES[lk.link_type] ?? ""}`}>{lk.link_type}</span></td>
                <td className="py-1.5 pr-3 text-gray-500 text-xs">{lk.note ?? "—"}</td>
                <td className="py-1.5 text-right"><button onClick={() => handleDelete(lk.id)} className="text-xs text-red-500 hover:text-red-700">Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export default function SourceDetail() {
  const { sourceId } = useParams<{ sourceId: string }>();
  const navigate = useNavigate();
  const isNew = sourceId === "new";
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [data, setData] = useState<Partial<AuthoritySource>>({
    source_code: "", source_type: "code_section", source_rank: "controlling",
    jurisdiction_code: "FED", entity_type_code: "shared", title: "", citation: "",
    issuer: "IRS", current_status: "active", is_substantive_authority: false,
    is_filing_authority: false, is_internal_only: false, requires_human_review: true,
    trust_score: null, official_url: "", checksum_sha256: "", notes: "",
    tax_year_start: null, tax_year_end: null, publication_date: null,
    effective_date_start: null, effective_date_end: null,
  });

  useEffect(() => {
    if (isNew || !sourceId) return;
    void (async () => {
      try {
        const s = await api.get<AuthoritySource>(`/sources/${sourceId}/`);
        setData(s);
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    })();
  }, [sourceId, isNew]);

  function handleChange(field: string, value: unknown) {
    setData(prev => ({ ...prev, [field]: value }));
    setSaved(false);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault(); setSaving(true);
    try {
      if (isNew) {
        const created = await api.post<AuthoritySource>("/sources/", data);
        navigate(`/sources/${created.id}`, { replace: true });
      } else {
        await api.patch(`/sources/${sourceId}/`, data);
        setSaved(true);
      }
    } catch (err) { console.error(err); }
    finally { setSaving(false); }
  }

  function autoGenCode() {
    const code = genSourceCode(data.jurisdiction_code ?? "FED", data.source_type ?? "", data.title ?? "");
    handleChange("source_code", code);
  }

  if (loading) return <div className="flex items-center justify-center h-full text-gray-400">Loading...</div>;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <button onClick={() => navigate("/sources")} className="text-sm text-blue-600 hover:text-blue-800 mb-1">← Back to Source Library</button>
          <h1 className="text-xl font-bold text-gray-800">{isNew ? "New Source" : (data.source_code ?? "Source")}</h1>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Section 1: Identity */}
        <section className="rounded border border-gray-200 bg-white p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Identity</h2>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className={labelClass}>Source Code</label>
              <div className="flex gap-1">
                <input type="text" value={data.source_code ?? ""} onChange={e => handleChange("source_code", e.target.value)} className={`${inputClass} flex-1`} required />
                {isNew && <button type="button" onClick={autoGenCode} className="rounded border border-gray-300 px-2 text-xs hover:bg-gray-100" title="Auto-generate">Auto</button>}
              </div>
            </div>
            <div><label className={labelClass}>Source Type</label><select value={data.source_type ?? ""} onChange={e => handleChange("source_type", e.target.value)} className={inputClass}>{SOURCE_TYPES.map(st => <option key={st} value={st}>{st.replace(/_/g, " ")}</option>)}</select></div>
            <div><label className={labelClass}>Source Rank</label><select value={data.source_rank ?? ""} onChange={e => handleChange("source_rank", e.target.value)} className={inputClass}>{SOURCE_RANKS.map(sr => <option key={sr} value={sr}>{sr.replace(/_/g, " ")}</option>)}</select></div>
          </div>
          <div className="grid grid-cols-1 gap-3 mt-3">
            <div><label className={labelClass}>Title</label><input type="text" value={data.title ?? ""} onChange={e => handleChange("title", e.target.value)} className={inputClass} required /></div>
          </div>
          <div className="grid grid-cols-3 gap-3 mt-3">
            <div><label className={labelClass}>Citation</label><input type="text" value={data.citation ?? ""} onChange={e => handleChange("citation", e.target.value || null)} className={inputClass} placeholder="IRC §1231(a)(1)" /></div>
            <div><label className={labelClass}>Jurisdiction</label><input type="text" value={data.jurisdiction_code ?? ""} onChange={e => handleChange("jurisdiction_code", e.target.value)} className={inputClass} placeholder="FED" required /></div>
            <div><label className={labelClass}>Entity Type</label><input type="text" value={data.entity_type_code ?? ""} onChange={e => handleChange("entity_type_code", e.target.value || null)} className={inputClass} placeholder="shared" /></div>
          </div>
          <div className="grid grid-cols-2 gap-3 mt-3">
            <div><label className={labelClass}>Issuer</label><input type="text" value={data.issuer ?? ""} onChange={e => handleChange("issuer", e.target.value)} className={inputClass} placeholder="IRS" required /></div>
            <div><label className={labelClass}>Status</label><select value={data.current_status ?? "active"} onChange={e => handleChange("current_status", e.target.value)} className={inputClass}>{STATUSES.map(s => <option key={s} value={s}>{s}</option>)}</select></div>
          </div>
        </section>

        {/* Section 2: Dates & Scope */}
        <section className="rounded border border-gray-200 bg-white p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Dates & Scope</h2>
          <div className="grid grid-cols-4 gap-3">
            <div><label className={labelClass}>Tax Year Start</label><input type="number" value={data.tax_year_start ?? ""} onChange={e => handleChange("tax_year_start", e.target.value ? Number(e.target.value) : null)} className={inputClass} /></div>
            <div><label className={labelClass}>Tax Year End</label><input type="number" value={data.tax_year_end ?? ""} onChange={e => handleChange("tax_year_end", e.target.value ? Number(e.target.value) : null)} className={inputClass} /></div>
            <div><label className={labelClass}>Publication Date</label><input type="date" value={data.publication_date ?? ""} onChange={e => handleChange("publication_date", e.target.value || null)} className={inputClass} /></div>
            <div />
          </div>
          <div className="grid grid-cols-2 gap-3 mt-3">
            <div><label className={labelClass}>Effective Date Start</label><input type="date" value={data.effective_date_start ?? ""} onChange={e => handleChange("effective_date_start", e.target.value || null)} className={inputClass} /></div>
            <div><label className={labelClass}>Effective Date End</label><input type="date" value={data.effective_date_end ?? ""} onChange={e => handleChange("effective_date_end", e.target.value || null)} className={inputClass} /></div>
          </div>
        </section>

        {/* Section 3: Quality Flags */}
        <section className="rounded border border-gray-200 bg-white p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Quality Flags</h2>
          <div className="flex flex-wrap gap-6">
            {([["is_substantive_authority", "Substantive Authority"], ["is_filing_authority", "Filing Authority"], ["is_internal_only", "Internal Only"], ["requires_human_review", "Requires Human Review"]] as const).map(([field, label]) => (
              <label key={field} className="flex items-center gap-1.5 text-sm">
                <input type="checkbox" checked={(data as Record<string, unknown>)[field] as boolean ?? false} onChange={e => handleChange(field, e.target.checked)} className="rounded border-gray-300" />{label}
              </label>
            ))}
          </div>
          <div className="mt-3 w-40">
            <label className={labelClass}>Trust Score (0–10)</label>
            <input type="number" step="0.01" min="0" max="10" value={data.trust_score ?? ""} onChange={e => handleChange("trust_score", e.target.value ? Number(e.target.value) : null)} className={inputClass} />
          </div>
        </section>

        {/* Section 4: Links & Notes */}
        <section className="rounded border border-gray-200 bg-white p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Links & Notes</h2>
          <div className="space-y-3">
            <div>
              <label className={labelClass}>Official URL</label>
              <div className="flex gap-2">
                <input type="text" value={data.official_url ?? ""} onChange={e => handleChange("official_url", e.target.value || null)} className={`${inputClass} flex-1`} />
                {data.official_url && <a href={data.official_url} target="_blank" rel="noopener noreferrer" className="rounded border border-gray-300 px-2 py-1 text-xs hover:bg-gray-100">Open</a>}
              </div>
            </div>
            <div><label className={labelClass}>Notes</label><textarea value={data.notes ?? ""} onChange={e => handleChange("notes", e.target.value || null)} className={`${inputClass} min-h-[60px]`} rows={3} /></div>
          </div>
        </section>

        {/* Save Button */}
        <div className="flex items-center gap-3">
          <button type="submit" disabled={saving} className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors">
            {saving ? "Saving..." : isNew ? "Create Source" : "Save Changes"}
          </button>
          {saved && <span className="text-sm text-green-600">Saved successfully.</span>}
        </div>
      </form>

      {/* Sections only visible on existing sources */}
      {!isNew && sourceId && (
        <div className="mt-8 space-y-6">
          <section className="rounded border border-gray-200 bg-white p-4"><ExcerptsSection sourceId={sourceId} /></section>
          <section className="rounded border border-gray-200 bg-white p-4"><VersionsSection sourceId={sourceId} /></section>
          <section className="rounded border border-gray-200 bg-white p-4"><TopicTagsSection sourceId={sourceId} /></section>
          <section className="rounded border border-gray-200 bg-white p-4"><FormLinksSection sourceId={sourceId} /></section>
        </div>
      )}
    </div>
  );
}
