import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { AuthorityTopic, PaginatedResponse } from "../types";

export default function TopicManager() {
  const [topics, setTopics] = useState<AuthorityTopic[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editData, setEditData] = useState<Partial<AuthorityTopic>>({});
  const [showAdd, setShowAdd] = useState(false);
  const [saving, setSaving] = useState(false);
  const [newTopic, setNewTopic] = useState({ topic_code: "", topic_name: "", description: "", parent_topic: null as string | null });

  const fetchTopics = useCallback(async () => {
    try {
      const d = await api.get<PaginatedResponse<AuthorityTopic>>("/topics/?page_size=200");
      setTopics(d.results);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void fetchTopics(); }, [fetchTopics]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault(); setSaving(true);
    try {
      await api.post("/topics/", { ...newTopic, parent_topic: newTopic.parent_topic || null, description: newTopic.description || null });
      setNewTopic({ topic_code: "", topic_name: "", description: "", parent_topic: null });
      setShowAdd(false); await fetchTopics();
    } catch (err) { console.error(err); } finally { setSaving(false); }
  }

  function startEdit(topic: AuthorityTopic) {
    setEditingId(topic.id);
    setEditData({ topic_code: topic.topic_code, topic_name: topic.topic_name, description: topic.description, parent_topic: topic.parent_topic });
  }

  async function handleSaveEdit() {
    if (!editingId) return; setSaving(true);
    try { await api.patch(`/topics/${editingId}/`, { ...editData, parent_topic: editData.parent_topic || null }); setEditingId(null); await fetchTopics(); }
    catch (err) { console.error(err); } finally { setSaving(false); }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this topic?")) return;
    try { await api.delete(`/topics/${id}/`); await fetchTopics(); } catch (err) { console.error(err); }
  }

  // Build tree
  const topicMap = new Map(topics.map(t => [t.id, t]));
  const rootTopics = topics.filter(t => !t.parent_topic);
  const childrenOf = (parentId: string) => topics.filter(t => t.parent_topic === parentId);

  function getDepth(topic: AuthorityTopic): number {
    let depth = 0;
    let current = topic;
    while (current.parent_topic && topicMap.has(current.parent_topic)) {
      depth++;
      current = topicMap.get(current.parent_topic)!;
    }
    return depth;
  }

  // Flatten tree for display
  const flatTree: AuthorityTopic[] = [];
  function walk(parentId: string | null) {
    const children = parentId ? childrenOf(parentId) : rootTopics;
    for (const child of children) {
      flatTree.push(child);
      walk(child.id);
    }
  }
  walk(null);

  const inputClass = "w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none";

  if (loading) return <div className="flex items-center justify-center h-full text-gray-400">Loading topics...</div>;

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <div>
          <Link to="/sources" className="text-sm text-blue-600 hover:text-blue-800 mb-1 block">← Back to Source Library</Link>
          <h1 className="text-2xl font-bold text-gray-800">Topic Manager</h1>
        </div>
        <button onClick={() => setShowAdd(!showAdd)} className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors">+ Add Topic</button>
      </div>

      {showAdd && (
        <form onSubmit={handleAdd} className="mb-4 rounded border border-blue-200 bg-blue-50 p-4 space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <div><label className="block text-xs font-medium text-gray-600 mb-1">Topic Code</label><input type="text" value={newTopic.topic_code} onChange={e => setNewTopic({...newTopic, topic_code: e.target.value})} className={inputClass} placeholder="macrs" required /></div>
            <div><label className="block text-xs font-medium text-gray-600 mb-1">Topic Name</label><input type="text" value={newTopic.topic_name} onChange={e => setNewTopic({...newTopic, topic_name: e.target.value})} className={inputClass} placeholder="MACRS" required /></div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Parent Topic</label>
              <select value={newTopic.parent_topic ?? ""} onChange={e => setNewTopic({...newTopic, parent_topic: e.target.value || null})} className={inputClass}>
                <option value="">None (root)</option>
                {topics.map(t => <option key={t.id} value={t.id}>{t.topic_name}</option>)}
              </select>
            </div>
          </div>
          <div><label className="block text-xs font-medium text-gray-600 mb-1">Description</label><input type="text" value={newTopic.description} onChange={e => setNewTopic({...newTopic, description: e.target.value})} className={inputClass} /></div>
          <div className="flex gap-2">
            <button type="submit" disabled={saving} className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:opacity-50">{saving ? "Adding..." : "Add Topic"}</button>
            <button type="button" onClick={() => setShowAdd(false)} className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-100">Cancel</button>
          </div>
        </form>
      )}

      <div className="rounded border border-gray-200 bg-white">
        {flatTree.map(topic => {
          const depth = getDepth(topic);
          const isEditing = editingId === topic.id;
          return (
            <div key={topic.id} className="flex items-center justify-between border-b border-gray-100 px-4 py-2 hover:bg-gray-50" style={{ paddingLeft: `${16 + depth * 24}px` }}>
              {isEditing ? (
                <div className="flex-1 flex gap-2 items-center">
                  <input type="text" value={editData.topic_code ?? ""} onChange={e => setEditData({...editData, topic_code: e.target.value})} className="rounded border border-gray-300 px-2 py-1 text-sm w-32" />
                  <input type="text" value={editData.topic_name ?? ""} onChange={e => setEditData({...editData, topic_name: e.target.value})} className="rounded border border-gray-300 px-2 py-1 text-sm flex-1" />
                  <select value={editData.parent_topic ?? ""} onChange={e => setEditData({...editData, parent_topic: e.target.value || null})} className="rounded border border-gray-300 px-2 py-1 text-sm w-40">
                    <option value="">None</option>
                    {topics.filter(t => t.id !== topic.id).map(t => <option key={t.id} value={t.id}>{t.topic_name}</option>)}
                  </select>
                  <button onClick={() => void handleSaveEdit()} disabled={saving} className="text-xs text-blue-600 hover:text-blue-800 font-medium">Save</button>
                  <button onClick={() => setEditingId(null)} className="text-xs text-gray-400 hover:text-gray-600">Cancel</button>
                </div>
              ) : (
                <>
                  <div className="flex items-center gap-2">
                    {depth > 0 && <span className="text-gray-300 text-xs">└</span>}
                    <span className="font-mono text-xs text-gray-500">{topic.topic_code}</span>
                    <span className="text-sm text-gray-800">{topic.topic_name}</span>
                    {topic.description && <span className="text-xs text-gray-400">— {topic.description}</span>}
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => startEdit(topic)} className="text-xs text-blue-600 hover:text-blue-800">Edit</button>
                    <button onClick={() => handleDelete(topic.id)} className="text-xs text-red-500 hover:text-red-700">Delete</button>
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
