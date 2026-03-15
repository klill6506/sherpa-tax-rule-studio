import { useCallback, useEffect, useMemo, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import ImportDialog from "./ImportDialog";
import type { PaginatedResponse, TaxForm } from "../types";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-200 text-gray-700",
  review: "bg-yellow-100 text-yellow-800",
  approved: "bg-green-100 text-green-800",
  archived: "bg-red-100 text-red-700",
};

interface NewFormData {
  jurisdiction: string;
  form_number: string;
  form_title: string;
  tax_year: number;
  entity_types: string[];
}

export default function Sidebar() {
  const navigate = useNavigate();
  const [forms, setForms] = useState<TaxForm[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [newForm, setNewForm] = useState<NewFormData>({
    jurisdiction: "federal",
    form_number: "",
    form_title: "",
    tax_year: 2025,
    entity_types: [],
  });

  const fetchForms = useCallback(async () => {
    try {
      const data = await api.get<PaginatedResponse<TaxForm>>("/forms/");
      setForms(data.results);
    } catch (err) {
      console.error("Failed to fetch forms:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchForms();
  }, [fetchForms]);

  const grouped = useMemo(() => {
    const map = new Map<string, TaxForm[]>();
    for (const form of forms) {
      const key = form.jurisdiction.toUpperCase() === "FEDERAL" ? "Federal" : form.jurisdiction.toUpperCase();
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(form);
    }
    return [...map.entries()].sort(([a], [b]) => {
      if (a === "Federal") return -1;
      if (b === "Federal") return 1;
      return a.localeCompare(b);
    });
  }, [forms]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    try {
      const created = await api.post<TaxForm>("/forms/", {
        ...newForm,
        status: "draft",
        version: 1,
        notes: "",
      });
      setShowCreate(false);
      setNewForm({ jurisdiction: "federal", form_number: "", form_title: "", tax_year: 2025, entity_types: [] });
      await fetchForms();
      navigate(`/forms/${created.id}`);
    } catch (err) {
      console.error("Failed to create form:", err);
    } finally {
      setCreating(false);
    }
  }

  return (
    <aside className="w-64 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <NavLink to="/" className="text-lg font-bold text-gray-800 hover:text-gray-600">
          Rule Studio
        </NavLink>
        <div className="mt-2 flex gap-1.5">
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="flex-1 rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
          >
            + New Form
          </button>
          <button
            onClick={() => setShowImport(true)}
            className="rounded border border-gray-300 px-2.5 py-1.5 text-sm text-gray-600 hover:bg-gray-100 transition-colors"
            title="Import JSON spec"
          >
            Import
          </button>
        </div>
      </div>

      {showImport && <ImportDialog onClose={() => { setShowImport(false); void fetchForms(); }} />}

      {/* New Form Panel */}
      {showCreate && (
        <form onSubmit={handleCreate} className="p-3 border-b border-gray-200 bg-blue-50 space-y-2">
          <select
            value={newForm.jurisdiction}
            onChange={(e) => setNewForm({ ...newForm, jurisdiction: e.target.value })}
            className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
          >
            <option value="federal">Federal</option>
            <option value="GA">Georgia (GA)</option>
            <option value="CA">California (CA)</option>
            <option value="NY">New York (NY)</option>
            <option value="TX">Texas (TX)</option>
            <option value="FL">Florida (FL)</option>
          </select>
          <input
            type="text"
            placeholder="Form number (e.g. 4797)"
            value={newForm.form_number}
            onChange={(e) => setNewForm({ ...newForm, form_number: e.target.value })}
            className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
            required
          />
          <input
            type="text"
            placeholder="Form title"
            value={newForm.form_title}
            onChange={(e) => setNewForm({ ...newForm, form_title: e.target.value })}
            className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
            required
          />
          <input
            type="number"
            placeholder="Tax year"
            value={newForm.tax_year}
            onChange={(e) => setNewForm({ ...newForm, tax_year: Number(e.target.value) })}
            className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
            required
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={creating}
              className="flex-1 rounded bg-blue-600 px-2 py-1 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {creating ? "Creating..." : "Create"}
            </button>
            <button
              type="button"
              onClick={() => setShowCreate(false)}
              className="rounded border border-gray-300 px-2 py-1 text-sm hover:bg-gray-100"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Form Tree */}
      <nav className="flex-1 overflow-y-auto p-2">
        {loading ? (
          <div className="p-4 text-sm text-gray-400">Loading forms...</div>
        ) : forms.length === 0 ? (
          <div className="p-4 text-sm text-gray-400">No forms yet. Create one to get started.</div>
        ) : (
          grouped.map(([jurisdiction, jurisdictionForms]) => (
            <div key={jurisdiction} className="mb-3">
              <div className="px-2 py-1 text-xs font-semibold uppercase tracking-wider text-gray-500">
                {jurisdiction}
              </div>
              {jurisdictionForms.map((form) => (
                <NavLink
                  key={form.id}
                  to={`/forms/${form.id}`}
                  className={({ isActive }) =>
                    `flex items-center justify-between rounded px-2 py-1.5 text-sm transition-colors ${
                      isActive ? "bg-blue-50 text-blue-700 font-medium" : "text-gray-700 hover:bg-gray-100"
                    }`
                  }
                >
                  <span className="truncate">{form.form_number}</span>
                  <span className={`ml-1 rounded px-1.5 py-0.5 text-xs ${STATUS_COLORS[form.status] ?? ""}`}>
                    {form.status}
                  </span>
                </NavLink>
              ))}
            </div>
          ))
        )}
      </nav>

      {/* Source Library Links */}
      <div className="border-t border-gray-200 p-2 space-y-0.5">
        <NavLink
          to="/sources"
          className={({ isActive }) =>
            `flex items-center gap-2 rounded px-3 py-2 text-sm transition-colors ${
              isActive ? "bg-purple-50 text-purple-700 font-medium" : "text-gray-600 hover:bg-gray-100"
            }`
          }
        >
          <span>Source Library</span>
        </NavLink>
        <NavLink
          to="/topics"
          className={({ isActive }) =>
            `flex items-center gap-2 rounded px-3 py-1.5 text-xs transition-colors ml-3 ${
              isActive ? "bg-purple-50 text-purple-700 font-medium" : "text-gray-500 hover:bg-gray-100"
            }`
          }
        >
          <span>Topics</span>
        </NavLink>
        <NavLink
          to="/feeds"
          className={({ isActive }) =>
            `flex items-center gap-2 rounded px-3 py-1.5 text-xs transition-colors ml-3 ${
              isActive ? "bg-purple-50 text-purple-700 font-medium" : "text-gray-500 hover:bg-gray-100"
            }`
          }
        >
          <span>Feeds</span>
        </NavLink>
      </div>
    </aside>
  );
}
