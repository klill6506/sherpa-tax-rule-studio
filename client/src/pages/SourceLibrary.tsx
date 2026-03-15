import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { AuthorityExcerpt, AuthoritySource, AuthorityTopic, PaginatedResponse } from "../types";

const RANK_COLORS: Record<string, string> = {
  controlling: "bg-red-100 text-red-800",
  primary_official: "bg-blue-100 text-blue-800",
  implementation_official: "bg-cyan-100 text-cyan-800",
  internal_interpretation: "bg-yellow-100 text-yellow-800",
  reference_only: "bg-gray-100 text-gray-600",
};
const STATUS_COLORS: Record<string, string> = {
  active: "bg-green-100 text-green-700",
  superseded: "bg-orange-100 text-orange-700",
  draft: "bg-gray-200 text-gray-600",
  archived: "bg-red-100 text-red-700",
};

export default function SourceLibrary() {
  const navigate = useNavigate();
  const [sources, setSources] = useState<AuthoritySource[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [jurisdictionFilter, setJurisdictionFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [rankFilter, setRankFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [entityFilter, setEntityFilter] = useState("");
  const [topicFilter, setTopicFilter] = useState("");
  const [topics, setTopics] = useState<AuthorityTopic[]>([]);

  // Excerpt search state
  const [excerptQuery, setExcerptQuery] = useState("");
  const [excerptResults, setExcerptResults] = useState<AuthorityExcerpt[]>([]);
  const [excerptSearching, setExcerptSearching] = useState(false);
  const [showExcerptSearch, setShowExcerptSearch] = useState(false);

  // Fetch topics for filter dropdown
  useEffect(() => {
    void (async () => {
      try { const d = await api.get<PaginatedResponse<AuthorityTopic>>("/topics/?page_size=200"); setTopics(d.results); }
      catch { /* ignore */ }
    })();
  }, []);

  const fetchSources = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.set("q", search);
      if (jurisdictionFilter) params.set("jurisdiction", jurisdictionFilter);
      if (typeFilter) params.set("source_type", typeFilter);
      if (rankFilter) params.set("source_rank", rankFilter);
      if (statusFilter) params.set("status", statusFilter);
      if (entityFilter) params.set("entity_type", entityFilter);
      if (topicFilter) params.set("topic", topicFilter);
      const qs = params.toString() ? `?${params.toString()}` : "";
      const data = await api.get<PaginatedResponse<AuthoritySource>>(`/sources/${qs}`);
      setSources(data.results);
    } catch (err) {
      console.error("Failed to fetch sources:", err);
    } finally {
      setLoading(false);
    }
  }, [search, jurisdictionFilter, typeFilter, rankFilter, statusFilter, entityFilter, topicFilter]);

  useEffect(() => {
    setLoading(true);
    const timer = setTimeout(() => { void fetchSources(); }, 300);
    return () => clearTimeout(timer);
  }, [fetchSources]);

  async function handleExcerptSearch() {
    if (!excerptQuery.trim()) return;
    setExcerptSearching(true);
    try {
      const data = await api.get<PaginatedResponse<AuthorityExcerpt>>(`/excerpts/search/?q=${encodeURIComponent(excerptQuery)}`);
      setExcerptResults(data.results);
    } catch (err) { console.error(err); }
    finally { setExcerptSearching(false); }
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-800">Source Library</h1>
        <div className="flex items-center gap-3">
          <Link to="/topics" className="rounded border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-100 transition-colors">Manage Topics</Link>
          <Link to="/feeds" className="rounded border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-100 transition-colors">Feed Definitions</Link>
          <button onClick={() => navigate("/sources/new")} className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors">+ New Source</button>
        </div>
      </div>

      {/* Global Excerpt Search Toggle */}
      <div className="mb-4">
        <button
          onClick={() => setShowExcerptSearch(!showExcerptSearch)}
          className={`text-sm font-medium ${showExcerptSearch ? "text-purple-700" : "text-purple-500 hover:text-purple-700"}`}
        >
          {showExcerptSearch ? "▼ Hide Excerpt Search" : "▶ Search Excerpts (full-text across all sources)"}
        </button>
        {showExcerptSearch && (
          <div className="mt-2 rounded border border-purple-200 bg-purple-50 p-4">
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                placeholder="Search all excerpts — e.g. 'recapture' or '1231 property'..."
                value={excerptQuery}
                onChange={e => setExcerptQuery(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter") void handleExcerptSearch(); }}
                className="flex-1 rounded border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500 focus:outline-none"
              />
              <button onClick={() => void handleExcerptSearch()} disabled={excerptSearching} className="rounded bg-purple-600 px-4 py-2 text-sm text-white hover:bg-purple-700 disabled:opacity-50">
                {excerptSearching ? "Searching..." : "Search"}
              </button>
            </div>
            {excerptResults.length > 0 && (
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {excerptResults.map(ex => (
                  <Link key={ex.id} to={`/sources/${ex.authority_source}`} className="block rounded border border-gray-200 bg-white px-3 py-2 hover:border-purple-300 transition-colors">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs text-gray-500">{ex.source_code}</span>
                      <span className="text-xs text-gray-400">{ex.source_title}</span>
                      {ex.excerpt_label && <span className="text-xs text-purple-600">— {ex.excerpt_label}</span>}
                    </div>
                    <p className="text-sm text-gray-700 line-clamp-2">{ex.excerpt_text}</p>
                    {ex.topic_tags.length > 0 && (
                      <div className="flex gap-1 mt-1">{ex.topic_tags.map(t => <span key={t} className="rounded bg-gray-100 px-1 py-0.5 text-xs text-gray-500">{t}</span>)}</div>
                    )}
                  </Link>
                ))}
              </div>
            )}
            {excerptResults.length === 0 && excerptQuery && !excerptSearching && (
              <p className="text-xs text-gray-400">No excerpts found for "{excerptQuery}".</p>
            )}
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-4">
        <input
          type="text" placeholder="Search sources..." value={search}
          onChange={e => setSearch(e.target.value)}
          className="flex-1 min-w-[200px] rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
        />
        <select value={jurisdictionFilter} onChange={e => setJurisdictionFilter(e.target.value)} className="rounded border border-gray-300 px-2 py-2 text-sm">
          <option value="">All Jurisdictions</option>
          <option value="FED">Federal</option><option value="GA">Georgia</option><option value="CA">California</option><option value="NY">New York</option>
        </select>
        <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} className="rounded border border-gray-300 px-2 py-2 text-sm">
          <option value="">All Types</option>
          <option value="code_section">IRC Section</option><option value="regulation">Regulation</option>
          <option value="official_instruction">Instructions</option><option value="official_publication">Publication</option>
          <option value="mef_business_rule">MeF Rule</option><option value="state_statute">State Statute</option>
          <option value="internal_memo">Internal Memo</option>
        </select>
        <select value={rankFilter} onChange={e => setRankFilter(e.target.value)} className="rounded border border-gray-300 px-2 py-2 text-sm">
          <option value="">All Ranks</option>
          <option value="controlling">Controlling</option><option value="primary_official">Primary Official</option>
          <option value="implementation_official">Implementation</option><option value="internal_interpretation">Internal</option>
        </select>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="rounded border border-gray-300 px-2 py-2 text-sm">
          <option value="">All Statuses</option>
          <option value="active">Active</option><option value="superseded">Superseded</option><option value="draft">Draft</option>
        </select>
        <select value={entityFilter} onChange={e => setEntityFilter(e.target.value)} className="rounded border border-gray-300 px-2 py-2 text-sm">
          <option value="">All Entity Types</option>
          <option value="shared">Shared</option><option value="1040">1040</option><option value="1120S">1120S</option><option value="1065">1065</option><option value="1120">1120</option>
        </select>
        {topics.length > 0 && (
          <select value={topicFilter} onChange={e => setTopicFilter(e.target.value)} className="rounded border border-gray-300 px-2 py-2 text-sm">
            <option value="">All Topics</option>
            {topics.map(t => <option key={t.id} value={t.topic_code}>{t.topic_name}</option>)}
          </select>
        )}
      </div>

      {/* Source Count */}
      <div className="text-xs text-gray-400 mb-3">{sources.length} source{sources.length !== 1 ? "s" : ""}</div>

      {/* Source List */}
      {loading ? (
        <div className="text-sm text-gray-400">Loading sources...</div>
      ) : sources.length === 0 ? (
        <div className="rounded border border-gray-200 bg-white p-8 text-center text-gray-400 text-sm">
          {search || jurisdictionFilter || typeFilter || rankFilter || statusFilter || entityFilter || topicFilter
            ? "No sources match your filters."
            : "No sources yet. Click \"+ New Source\" to create one."}
        </div>
      ) : (
        <div className="space-y-2">
          {sources.map(source => (
            <Link
              key={source.id}
              to={`/sources/${source.id}`}
              className="block rounded border border-gray-200 bg-white p-4 hover:border-blue-300 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-sm font-medium text-gray-800">{source.source_code}</span>
                    <span className={`rounded px-1.5 py-0.5 text-xs ${RANK_COLORS[source.source_rank] ?? ""}`}>{source.source_rank.replace(/_/g, " ")}</span>
                    <span className={`rounded px-1.5 py-0.5 text-xs ${STATUS_COLORS[source.current_status] ?? ""}`}>{source.current_status}</span>
                  </div>
                  <p className="text-sm text-gray-600">{source.title}</p>
                  {source.citation && <p className="text-xs text-gray-400 mt-0.5">{source.citation}</p>}
                </div>
                <div className="text-right text-xs text-gray-400 ml-4 shrink-0">
                  <div>{source.jurisdiction_code}</div>
                  <div>{source.issuer}</div>
                  {source.tax_year_start && <div>TY {source.tax_year_start}{source.tax_year_end && source.tax_year_end !== source.tax_year_start ? `–${source.tax_year_end}` : ""}</div>}
                  {source.excerpt_count != null && source.excerpt_count > 0 && (
                    <div className="mt-1 text-purple-600">{source.excerpt_count} excerpt{source.excerpt_count !== 1 ? "s" : ""}</div>
                  )}
                </div>
              </div>
              {source.topics && source.topics.length > 0 && (
                <div className="flex gap-1 mt-2">{source.topics.map(topic => (
                  <span key={topic} className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500">{topic}</span>
                ))}</div>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
