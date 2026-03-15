import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { AuthoritySource, PaginatedResponse } from "../types";

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
  const [sources, setSources] = useState<AuthoritySource[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [jurisdictionFilter, setJurisdictionFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  const fetchSources = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.set("q", search);
      if (jurisdictionFilter) params.set("jurisdiction", jurisdictionFilter);
      if (typeFilter) params.set("source_type", typeFilter);
      const qs = params.toString() ? `?${params.toString()}` : "";
      const data = await api.get<PaginatedResponse<AuthoritySource>>(`/sources/${qs}`);
      setSources(data.results);
    } catch (err) {
      console.error("Failed to fetch sources:", err);
    } finally {
      setLoading(false);
    }
  }, [search, jurisdictionFilter, typeFilter]);

  useEffect(() => {
    setLoading(true);
    const timer = setTimeout(() => {
      void fetchSources();
    }, 300);
    return () => clearTimeout(timer);
  }, [fetchSources]);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Source Library</h1>
        <span className="text-sm text-gray-400">{sources.length} sources</span>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="Search sources..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
        />
        <select
          value={jurisdictionFilter}
          onChange={(e) => setJurisdictionFilter(e.target.value)}
          className="rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">All Jurisdictions</option>
          <option value="FED">Federal</option>
          <option value="GA">Georgia</option>
          <option value="CA">California</option>
        </select>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">All Types</option>
          <option value="code_section">IRC Section</option>
          <option value="regulation">Treasury Regulation</option>
          <option value="official_instruction">Form Instructions</option>
          <option value="official_publication">IRS Publication</option>
          <option value="mef_business_rule">MeF Business Rule</option>
          <option value="state_statute">State Statute</option>
          <option value="internal_memo">Internal Memo</option>
        </select>
      </div>

      {/* Source List */}
      {loading ? (
        <div className="text-sm text-gray-400">Loading sources...</div>
      ) : sources.length === 0 ? (
        <div className="rounded border border-gray-200 bg-white p-8 text-center text-gray-400 text-sm">
          {search || jurisdictionFilter || typeFilter
            ? "No sources match your filters."
            : "No sources yet. Sources will be added as you author form specs."}
        </div>
      ) : (
        <div className="space-y-2">
          {sources.map((source) => (
            <div
              key={source.id}
              className="rounded border border-gray-200 bg-white p-4 hover:border-gray-300 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-sm font-medium text-gray-800">
                      {source.source_code}
                    </span>
                    <span className={`rounded px-1.5 py-0.5 text-xs ${RANK_COLORS[source.source_rank] ?? ""}`}>
                      {source.source_rank.replace(/_/g, " ")}
                    </span>
                    <span className={`rounded px-1.5 py-0.5 text-xs ${STATUS_COLORS[source.current_status] ?? ""}`}>
                      {source.current_status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{source.title}</p>
                  {source.citation && (
                    <p className="text-xs text-gray-400 mt-1">{source.citation}</p>
                  )}
                </div>
                <div className="text-right text-xs text-gray-400 ml-4">
                  <div>{source.jurisdiction_code}</div>
                  <div>{source.issuer}</div>
                  {source.excerpt_count != null && source.excerpt_count > 0 && (
                    <div className="mt-1 text-purple-600">{source.excerpt_count} excerpts</div>
                  )}
                </div>
              </div>
              {source.topics && source.topics.length > 0 && (
                <div className="flex gap-1 mt-2">
                  {source.topics.map((topic) => (
                    <span key={topic} className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500">
                      {topic}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
