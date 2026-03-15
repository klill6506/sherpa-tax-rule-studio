import type { TaxForm } from "../types";

const STATUS_OPTIONS = ["draft", "review", "approved", "archived"] as const;

const JURISDICTION_BADGE: Record<string, string> = {
  federal: "bg-blue-100 text-blue-800",
  default: "bg-purple-100 text-purple-800",
};

interface TopBarProps {
  form: TaxForm;
  onStatusChange: (status: TaxForm["status"]) => void;
  onExport: () => void;
}

export default function TopBar({ form, onStatusChange, onExport }: TopBarProps) {
  const jurisdictionClass =
    form.jurisdiction.toLowerCase() === "federal"
      ? JURISDICTION_BADGE.federal
      : JURISDICTION_BADGE.default;

  return (
    <div className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3">
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-semibold text-gray-800">{form.form_title}</h1>
        <span className={`rounded px-2 py-0.5 text-xs font-medium ${jurisdictionClass}`}>
          {form.jurisdiction.toUpperCase()}
        </span>
      </div>
      <div className="flex items-center gap-4 text-sm">
        <span className="text-gray-500">TY {form.tax_year}</span>
        <span className="text-gray-400">v{form.version}</span>
        <select
          value={form.status}
          onChange={(e) => onStatusChange(e.target.value as TaxForm["status"])}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        >
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </option>
          ))}
        </select>
        <button
          onClick={onExport}
          className="rounded bg-emerald-600 px-3 py-1 text-sm font-medium text-white hover:bg-emerald-700 transition-colors"
        >
          Export
        </button>
      </div>
    </div>
  );
}
