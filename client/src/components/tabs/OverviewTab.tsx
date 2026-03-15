import { useState } from "react";
import { api } from "../../api/client";
import type { TaxForm } from "../../types";

const ENTITY_TYPE_OPTIONS = ["1040", "1065", "1120", "1120S"];

interface OverviewTabProps {
  form: TaxForm;
  onUpdate: () => void;
}

export default function OverviewTab({ form, onUpdate }: OverviewTabProps) {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [formData, setFormData] = useState({
    jurisdiction: form.jurisdiction,
    form_number: form.form_number,
    form_title: form.form_title,
    entity_types: form.entity_types,
    tax_year: form.tax_year,
    version: form.version,
    notes: form.notes,
  });

  function handleChange(field: string, value: unknown) {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setSaved(false);
  }

  function toggleEntityType(type: string) {
    setFormData((prev) => ({
      ...prev,
      entity_types: prev.entity_types.includes(type)
        ? prev.entity_types.filter((t) => t !== type)
        : [...prev.entity_types, type],
    }));
    setSaved(false);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.patch(`/forms/${form.id}/`, formData);
      setSaved(true);
      onUpdate();
    } catch (err) {
      console.error("Failed to save:", err);
    } finally {
      setSaving(false);
    }
  }

  const inputClass =
    "w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none";

  return (
    <form onSubmit={handleSave} className="max-w-2xl space-y-5">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Jurisdiction</label>
          <select
            value={formData.jurisdiction}
            onChange={(e) => handleChange("jurisdiction", e.target.value)}
            className={inputClass}
          >
            <option value="federal">Federal</option>
            <option value="GA">Georgia (GA)</option>
            <option value="CA">California (CA)</option>
            <option value="NY">New York (NY)</option>
            <option value="TX">Texas (TX)</option>
            <option value="FL">Florida (FL)</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Form Number</label>
          <input
            type="text"
            value={formData.form_number}
            onChange={(e) => handleChange("form_number", e.target.value)}
            className={inputClass}
            required
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Form Title</label>
        <input
          type="text"
          value={formData.form_title}
          onChange={(e) => handleChange("form_title", e.target.value)}
          className={inputClass}
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Tax Year</label>
          <input
            type="number"
            value={formData.tax_year}
            onChange={(e) => handleChange("tax_year", Number(e.target.value))}
            className={inputClass}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Version</label>
          <input
            type="number"
            value={formData.version}
            onChange={(e) => handleChange("version", Number(e.target.value))}
            className={inputClass}
            min={1}
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Entity Types</label>
        <div className="flex gap-3">
          {ENTITY_TYPE_OPTIONS.map((type) => (
            <label key={type} className="flex items-center gap-1.5 text-sm">
              <input
                type="checkbox"
                checked={formData.entity_types.includes(type)}
                onChange={() => toggleEntityType(type)}
                className="rounded border-gray-300"
              />
              {type}
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
        <textarea
          value={formData.notes}
          onChange={(e) => handleChange("notes", e.target.value)}
          className={`${inputClass} min-h-[100px]`}
          rows={4}
        />
      </div>

      <div className="flex items-center gap-3 pt-2">
        <button
          type="submit"
          disabled={saving}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {saving ? "Saving..." : "Save Changes"}
        </button>
        {saved && <span className="text-sm text-green-600">Saved successfully.</span>}
      </div>

      {/* Metadata (read-only) */}
      <div className="border-t border-gray-200 pt-4 mt-6">
        <h3 className="text-sm font-medium text-gray-500 mb-2">Metadata</h3>
        <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
          <div>ID: {form.id}</div>
          <div>Status: {form.status}</div>
          <div>Created: {new Date(form.created_at).toLocaleString()}</div>
          <div>Updated: {new Date(form.updated_at).toLocaleString()}</div>
        </div>
      </div>
    </form>
  );
}
