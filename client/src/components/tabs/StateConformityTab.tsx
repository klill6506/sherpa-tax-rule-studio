import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import type { AuthoritySource, JurisdictionConformitySource, PaginatedResponse } from "../../types";

const CONFORMITY_TYPES = ["rolling", "static", "partial", "decoupled"] as const;
const CONFORMITY_BADGES: Record<string, string> = {
  rolling: "bg-green-100 text-green-700",
  static: "bg-blue-100 text-blue-700",
  partial: "bg-yellow-100 text-yellow-800",
  decoupled: "bg-red-100 text-red-700",
};

interface DecoupledItem {
  item: string;
  federal_treatment: string;
  state_treatment: string;
  authority_source_id: string | null;
  notes: string;
}

interface StateConformityTabProps {
  jurisdiction: string;
  taxYear: number;
}

export default function StateConformityTab({ jurisdiction, taxYear }: StateConformityTabProps) {
  const [record, setRecord] = useState<JurisdictionConformitySource | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [creating, setCreating] = useState(false);
  const [linkedSource, setLinkedSource] = useState<AuthoritySource | null>(null);

  // Edit state
  const [formData, setFormData] = useState({
    conformity_type: "partial" as JurisdictionConformitySource["conformity_type"],
    federal_reference_note: "",
    summary: "",
    authority_source: null as string | null,
    notes: "",
    decoupled_items: [] as DecoupledItem[],
  });

  // Source search for linking
  const [sourceSearch, setSourceSearch] = useState("");
  const [sourceResults, setSourceResults] = useState<AuthoritySource[]>([]);
  const [searchingSource, setSearchingSource] = useState(false);

  const fetchRecord = useCallback(async () => {
    try {
      const data = await api.get<PaginatedResponse<JurisdictionConformitySource>>(
        `/conformity/?jurisdiction=${encodeURIComponent(jurisdiction)}&tax_year=${taxYear}`
      );
      if (data.results.length > 0) {
        const rec = data.results[0]!;
        setRecord(rec);
        setFormData({
          conformity_type: rec.conformity_type,
          federal_reference_note: rec.federal_reference_note ?? "",
          summary: rec.summary ?? "",
          authority_source: rec.authority_source,
          notes: rec.notes ?? "",
          decoupled_items: (rec.decoupled_items as DecoupledItem[] | undefined) ?? [],
        });
        if (rec.authority_source) {
          try {
            const s = await api.get<AuthoritySource>(`/sources/${rec.authority_source}/`);
            setLinkedSource(s);
          } catch { /* ignore */ }
        }
      }
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, [jurisdiction, taxYear]);

  useEffect(() => { void fetchRecord(); }, [fetchRecord]);

  async function handleCreate() {
    setCreating(true);
    try {
      const created = await api.post<JurisdictionConformitySource>("/conformity/", {
        jurisdiction_code: jurisdiction,
        tax_year: taxYear,
        conformity_type: "partial",
        federal_reference_note: "",
        summary: "",
        notes: "",
        decoupled_items: [],
      });
      setRecord(created);
      setFormData({
        conformity_type: created.conformity_type,
        federal_reference_note: "",
        summary: "",
        authority_source: null,
        notes: "",
        decoupled_items: [],
      });
    } catch (err) { console.error(err); }
    finally { setCreating(false); }
  }

  async function handleSave() {
    if (!record) return;
    setSaving(true);
    try {
      await api.patch(`/conformity/${record.id}/`, {
        ...formData,
        federal_reference_note: formData.federal_reference_note || null,
        summary: formData.summary || null,
        notes: formData.notes || null,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) { console.error(err); }
    finally { setSaving(false); }
  }

  async function handleSearchSource() {
    if (!sourceSearch.trim()) return;
    setSearchingSource(true);
    try {
      const d = await api.get<PaginatedResponse<AuthoritySource>>(`/sources/?q=${encodeURIComponent(sourceSearch)}`);
      setSourceResults(d.results);
    } catch (err) { console.error(err); }
    finally { setSearchingSource(false); }
  }

  function selectSource(source: AuthoritySource) {
    setFormData({ ...formData, authority_source: source.id });
    setLinkedSource(source);
    setSourceResults([]);
    setSourceSearch("");
    setSaved(false);
  }

  function addDecoupledItem() {
    setFormData({
      ...formData,
      decoupled_items: [...formData.decoupled_items, { item: "", federal_treatment: "", state_treatment: "", authority_source_id: null, notes: "" }],
    });
    setSaved(false);
  }

  function updateDecoupledItem(index: number, field: keyof DecoupledItem, value: string | null) {
    const items = [...formData.decoupled_items];
    items[index] = { ...items[index]!, [field]: value };
    setFormData({ ...formData, decoupled_items: items });
    setSaved(false);
  }

  function removeDecoupledItem(index: number) {
    setFormData({ ...formData, decoupled_items: formData.decoupled_items.filter((_, i) => i !== index) });
    setSaved(false);
  }

  const inputClass = "w-full rounded border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none";

  if (loading) return <div className="text-gray-400 text-sm">Loading conformity data...</div>;

  if (!record) {
    return (
      <div className="rounded border border-gray-200 bg-white p-8 text-center">
        <p className="text-gray-500 mb-4">No conformity record found for {jurisdiction} TY{taxYear}.</p>
        <button onClick={() => void handleCreate()} disabled={creating} className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
          {creating ? "Creating..." : "Create Conformity Record"}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Conformity Summary Card */}
      <section className="rounded border border-gray-200 bg-white p-5">
        <div className="flex items-center gap-3 mb-4">
          <h2 className="text-lg font-semibold text-gray-800">{jurisdiction} Conformity</h2>
          <span className={`rounded px-2 py-0.5 text-xs font-medium ${CONFORMITY_BADGES[formData.conformity_type] ?? ""}`}>
            {formData.conformity_type}
          </span>
          <span className="text-sm text-gray-400">TY {taxYear}</span>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Conformity Type</label>
            <select value={formData.conformity_type} onChange={e => { setFormData({ ...formData, conformity_type: e.target.value as JurisdictionConformitySource["conformity_type"] }); setSaved(false); }} className={inputClass}>
              {CONFORMITY_TYPES.map(ct => <option key={ct} value={ct}>{ct.charAt(0).toUpperCase() + ct.slice(1)}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Federal Reference Note</label>
            <input type="text" value={formData.federal_reference_note} onChange={e => { setFormData({ ...formData, federal_reference_note: e.target.value }); setSaved(false); }} className={inputClass} placeholder="e.g., Georgia conforms to IRC as of January 1, 2025" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Summary</label>
            <textarea value={formData.summary} onChange={e => { setFormData({ ...formData, summary: e.target.value }); setSaved(false); }} className={`${inputClass} min-h-[80px]`} rows={3} />
          </div>

          {/* Linked Authority Source */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Authority Source</label>
            {linkedSource ? (
              <div className="flex items-center justify-between rounded border border-gray-200 px-3 py-2">
                <Link to={`/sources/${linkedSource.id}`} className="text-sm text-blue-600 hover:text-blue-800 font-medium">
                  {linkedSource.source_code}: {linkedSource.title}
                </Link>
                <button onClick={() => { setLinkedSource(null); setFormData({ ...formData, authority_source: null }); setSaved(false); }} className="text-xs text-gray-400 hover:text-gray-600">Remove</button>
              </div>
            ) : (
              <div className="space-y-1">
                <div className="flex gap-2">
                  <input type="text" value={sourceSearch} onChange={e => setSourceSearch(e.target.value)} onKeyDown={e => { if (e.key === "Enter") void handleSearchSource(); }} className={`${inputClass} flex-1`} placeholder="Search authority sources..." />
                  <button onClick={() => void handleSearchSource()} disabled={searchingSource} className="rounded bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50">{searchingSource ? "..." : "Search"}</button>
                </div>
                {sourceResults.length > 0 && (
                  <div className="max-h-32 overflow-y-auto rounded border border-gray-200 bg-white">
                    {sourceResults.map(s => (
                      <button key={s.id} onClick={() => selectSource(s)} className="w-full text-left px-3 py-1.5 text-sm hover:bg-blue-50 border-b border-gray-100 last:border-0">
                        <span className="font-mono text-xs text-gray-500">{s.source_code}</span>
                        <span className="ml-2 text-gray-700">{s.title}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
            <textarea value={formData.notes} onChange={e => { setFormData({ ...formData, notes: e.target.value }); setSaved(false); }} className={inputClass} rows={2} />
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button onClick={() => void handleSave()} disabled={saving} className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
              {saving ? "Saving..." : "Save Changes"}
            </button>
            {saved && <span className="text-sm text-green-600">Saved.</span>}
          </div>
        </div>
      </section>

      {/* Decoupled Items */}
      <section className="rounded border border-gray-200 bg-white p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-gray-800">Decoupled Items</h3>
          <button onClick={addDecoupledItem} className="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Add Item</button>
        </div>

        {formData.decoupled_items.length === 0 ? (
          <p className="text-sm text-gray-400 italic">No decoupled items. Click "Add Item" to document where this state diverges from federal treatment.</p>
        ) : (
          <div className="space-y-3">
            {formData.decoupled_items.map((item, idx) => (
              <div key={idx} className="rounded border border-gray-200 p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-gray-500">Item #{idx + 1}</span>
                  <button onClick={() => removeDecoupledItem(idx)} className="text-xs text-red-500 hover:text-red-700">Remove</button>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-0.5">Item</label>
                  <input type="text" value={item.item} onChange={e => updateDecoupledItem(idx, "item", e.target.value)} className={inputClass} placeholder="Bonus Depreciation (IRC §168(k))" />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-0.5">Federal Treatment</label>
                    <textarea value={item.federal_treatment} onChange={e => updateDecoupledItem(idx, "federal_treatment", e.target.value)} className={inputClass} rows={2} placeholder="100% under OBBBA..." />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-0.5">State Treatment</label>
                    <textarea value={item.state_treatment} onChange={e => updateDecoupledItem(idx, "state_treatment", e.target.value)} className={inputClass} rows={2} placeholder="Not allowed — state does not conform..." />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-0.5">Notes</label>
                  <input type="text" value={item.notes} onChange={e => updateDecoupledItem(idx, "notes", e.target.value)} className={inputClass} />
                </div>
              </div>
            ))}
            <div className="pt-2">
              <button onClick={() => void handleSave()} disabled={saving} className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
                {saving ? "Saving..." : "Save All Changes"}
              </button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
