import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { PaginatedResponse, SourceFeedDefinition } from "../types";

const FEED_TYPES = ["html_index", "pdf_list", "xml_repo", "manual_upload"] as const;

export default function FeedManager() {
  const [feeds, setFeeds] = useState<SourceFeedDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editData, setEditData] = useState<Partial<SourceFeedDefinition>>({});
  const [showAdd, setShowAdd] = useState(false);
  const [saving, setSaving] = useState(false);
  const [newFeed, setNewFeed] = useState({
    feed_code: "", feed_name: "", jurisdiction_code: "FED", source_family: "",
    base_url: "", feed_type: "html_index" as SourceFeedDefinition["feed_type"],
    refresh_frequency: "seasonal", parser_strategy: "html_scrape", is_active: true, notes: "",
  });

  const fetchFeeds = useCallback(async () => {
    try { const d = await api.get<PaginatedResponse<SourceFeedDefinition>>("/feeds/"); setFeeds(d.results); }
    catch (err) { console.error(err); } finally { setLoading(false); }
  }, []);

  useEffect(() => { void fetchFeeds(); }, [fetchFeeds]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault(); setSaving(true);
    try {
      await api.post("/feeds/", { ...newFeed, base_url: newFeed.base_url || null, notes: newFeed.notes || null });
      setNewFeed({ feed_code: "", feed_name: "", jurisdiction_code: "FED", source_family: "", base_url: "", feed_type: "html_index", refresh_frequency: "seasonal", parser_strategy: "html_scrape", is_active: true, notes: "" });
      setShowAdd(false); await fetchFeeds();
    } catch (err) { console.error(err); } finally { setSaving(false); }
  }

  function startEdit(feed: SourceFeedDefinition) {
    setEditingId(feed.id);
    setEditData({ feed_code: feed.feed_code, feed_name: feed.feed_name, jurisdiction_code: feed.jurisdiction_code, source_family: feed.source_family, base_url: feed.base_url, feed_type: feed.feed_type, refresh_frequency: feed.refresh_frequency, parser_strategy: feed.parser_strategy, is_active: feed.is_active, notes: feed.notes });
  }

  async function handleSaveEdit() {
    if (!editingId) return; setSaving(true);
    try { await api.patch(`/feeds/${editingId}/`, editData); setEditingId(null); await fetchFeeds(); }
    catch (err) { console.error(err); } finally { setSaving(false); }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this feed definition?")) return;
    try { await api.delete(`/feeds/${id}/`); await fetchFeeds(); } catch (err) { console.error(err); }
  }

  const inputClass = "w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none";
  const cellClass = "px-3 py-2 text-sm";

  if (loading) return <div className="flex items-center justify-center h-full text-gray-400">Loading feeds...</div>;

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <div>
          <Link to="/sources" className="text-sm text-blue-600 hover:text-blue-800 mb-1 block">← Back to Source Library</Link>
          <h1 className="text-2xl font-bold text-gray-800">Feed Definitions</h1>
          <p className="text-sm text-gray-500 mt-1">Source update feeds. Ingestion is a future feature — these define what the system is designed to track.</p>
        </div>
        <button onClick={() => setShowAdd(!showAdd)} className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors">+ Add Feed</button>
      </div>

      {showAdd && (
        <form onSubmit={handleAdd} className="mb-4 rounded border border-blue-200 bg-blue-50 p-4 space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <div><label className="block text-xs font-medium text-gray-600 mb-1">Feed Code</label><input type="text" value={newFeed.feed_code} onChange={e => setNewFeed({...newFeed, feed_code: e.target.value})} className={inputClass} required /></div>
            <div><label className="block text-xs font-medium text-gray-600 mb-1">Feed Name</label><input type="text" value={newFeed.feed_name} onChange={e => setNewFeed({...newFeed, feed_name: e.target.value})} className={inputClass} required /></div>
            <div><label className="block text-xs font-medium text-gray-600 mb-1">Jurisdiction</label><input type="text" value={newFeed.jurisdiction_code} onChange={e => setNewFeed({...newFeed, jurisdiction_code: e.target.value})} className={inputClass} required /></div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div><label className="block text-xs font-medium text-gray-600 mb-1">Source Family</label><input type="text" value={newFeed.source_family} onChange={e => setNewFeed({...newFeed, source_family: e.target.value})} className={inputClass} required /></div>
            <div><label className="block text-xs font-medium text-gray-600 mb-1">Feed Type</label><select value={newFeed.feed_type} onChange={e => setNewFeed({...newFeed, feed_type: e.target.value as SourceFeedDefinition["feed_type"]})} className={inputClass}>{FEED_TYPES.map(ft => <option key={ft} value={ft}>{ft.replace(/_/g, " ")}</option>)}</select></div>
            <div><label className="block text-xs font-medium text-gray-600 mb-1">Refresh</label><input type="text" value={newFeed.refresh_frequency} onChange={e => setNewFeed({...newFeed, refresh_frequency: e.target.value})} className={inputClass} /></div>
          </div>
          <div><label className="block text-xs font-medium text-gray-600 mb-1">Base URL</label><input type="text" value={newFeed.base_url} onChange={e => setNewFeed({...newFeed, base_url: e.target.value})} className={inputClass} /></div>
          <div className="flex gap-2">
            <button type="submit" disabled={saving} className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:opacity-50">{saving ? "Adding..." : "Add Feed"}</button>
            <button type="button" onClick={() => setShowAdd(false)} className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-100">Cancel</button>
          </div>
        </form>
      )}

      <div className="overflow-x-auto rounded border border-gray-200">
        <table className="w-full bg-white">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              <th className={`${cellClass} text-left font-medium text-gray-600`}>Feed Code</th>
              <th className={`${cellClass} text-left font-medium text-gray-600`}>Name</th>
              <th className={`${cellClass} text-center font-medium text-gray-600`}>Jurisdiction</th>
              <th className={`${cellClass} text-left font-medium text-gray-600`}>Family</th>
              <th className={`${cellClass} text-center font-medium text-gray-600`}>Type</th>
              <th className={`${cellClass} text-center font-medium text-gray-600`}>Refresh</th>
              <th className={`${cellClass} text-center font-medium text-gray-600`}>Active</th>
              <th className={`${cellClass} text-right font-medium text-gray-600`}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {feeds.map(feed => {
              const isEditing = editingId === feed.id;
              return (
                <tr key={feed.id} className="border-b border-gray-100 hover:bg-gray-50">
                  {isEditing ? (
                    <>
                      <td className={cellClass}><input type="text" value={editData.feed_code ?? ""} onChange={e => setEditData({...editData, feed_code: e.target.value})} className={inputClass} /></td>
                      <td className={cellClass}><input type="text" value={editData.feed_name ?? ""} onChange={e => setEditData({...editData, feed_name: e.target.value})} className={inputClass} /></td>
                      <td className={cellClass}><input type="text" value={editData.jurisdiction_code ?? ""} onChange={e => setEditData({...editData, jurisdiction_code: e.target.value})} className={`${inputClass} text-center`} /></td>
                      <td className={cellClass}><input type="text" value={editData.source_family ?? ""} onChange={e => setEditData({...editData, source_family: e.target.value})} className={inputClass} /></td>
                      <td className={cellClass}><select value={editData.feed_type ?? ""} onChange={e => setEditData({...editData, feed_type: e.target.value as SourceFeedDefinition["feed_type"]})} className={inputClass}>{FEED_TYPES.map(ft => <option key={ft} value={ft}>{ft.replace(/_/g, " ")}</option>)}</select></td>
                      <td className={cellClass}><input type="text" value={editData.refresh_frequency ?? ""} onChange={e => setEditData({...editData, refresh_frequency: e.target.value})} className={`${inputClass} text-center`} /></td>
                      <td className={`${cellClass} text-center`}><input type="checkbox" checked={editData.is_active ?? true} onChange={e => setEditData({...editData, is_active: e.target.checked})} className="rounded border-gray-300" /></td>
                      <td className={`${cellClass} text-right`}><button onClick={() => void handleSaveEdit()} disabled={saving} className="text-xs text-blue-600 hover:text-blue-800 font-medium mr-2">Save</button><button onClick={() => setEditingId(null)} className="text-xs text-gray-400 hover:text-gray-600">Cancel</button></td>
                    </>
                  ) : (
                    <>
                      <td className={`${cellClass} font-mono text-xs font-bold`}>{feed.feed_code}</td>
                      <td className={cellClass}>{feed.feed_name}</td>
                      <td className={`${cellClass} text-center`}>{feed.jurisdiction_code}</td>
                      <td className={`${cellClass} text-gray-500`}>{feed.source_family}</td>
                      <td className={`${cellClass} text-center`}><span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs">{feed.feed_type.replace(/_/g, " ")}</span></td>
                      <td className={`${cellClass} text-center text-gray-500`}>{feed.refresh_frequency}</td>
                      <td className={`${cellClass} text-center`}>{feed.is_active ? <span className="text-green-600 font-bold">✓</span> : <span className="text-gray-300">—</span>}</td>
                      <td className={`${cellClass} text-right`}>
                        <button onClick={() => startEdit(feed)} className="text-xs text-blue-600 hover:text-blue-800 font-medium mr-2">Edit</button>
                        <button onClick={() => handleDelete(feed.id)} className="text-xs text-red-500 hover:text-red-700">Delete</button>
                      </td>
                    </>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
