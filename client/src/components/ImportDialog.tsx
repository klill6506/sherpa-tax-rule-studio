import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

interface ImportResult {
  id: string;
  form_number: string;
  jurisdiction: string;
  tax_year: number;
  version: number;
  existing_version: number | null;
}

/* eslint-disable @typescript-eslint/no-explicit-any */
interface ImportDialogProps {
  onClose: () => void;
}

export default function ImportDialog({ onClose }: ImportDialogProps) {
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const [parsedData, setParsedData] = useState<any>(null);
  const [parseError, setParseError] = useState("");
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [importError, setImportError] = useState("");

  async function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setParseError("");
    setParsedData(null);
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      if (!data.metadata) {
        setParseError("Invalid spec file — missing metadata section.");
        return;
      }
      setParsedData(data);
    } catch {
      setParseError("Failed to parse JSON file.");
    }
  }

  async function handleImport() {
    if (!parsedData) return;
    setImporting(true);
    setImportError("");
    try {
      const res = await api.post<ImportResult>("/forms/import_spec/", parsedData);
      setResult(res);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setImporting(false);
    }
  }

  const meta = parsedData?.metadata;
  const factCount = parsedData?.facts?.length ?? 0;
  const ruleCount = parsedData?.rules?.length ?? 0;
  const lineCount = parsedData?.line_map?.length ?? 0;
  const diagCount = parsedData?.diagnostics?.length ?? 0;
  const testCount = parsedData?.tests?.length ?? 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Import Spec File</h2>

        {!result ? (
          <>
            {/* File Picker */}
            <div className="mb-4">
              <input
                ref={fileRef}
                type="file"
                accept=".json"
                onChange={handleFileSelect}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
              {parseError && <p className="text-sm text-red-500 mt-2">{parseError}</p>}
            </div>

            {/* Preview */}
            {meta && (
              <div className="rounded border border-gray-200 bg-gray-50 p-4 mb-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Preview</h3>
                <div className="text-sm space-y-1">
                  <p><span className="text-gray-500">Form:</span> {meta.form_number} — {meta.form_title}</p>
                  <p><span className="text-gray-500">Jurisdiction:</span> {meta.jurisdiction}</p>
                  <p><span className="text-gray-500">Tax Year:</span> {meta.tax_year}</p>
                  <p className="text-gray-500 mt-2">
                    {factCount} facts, {ruleCount} rules, {lineCount} lines, {diagCount} diagnostics, {testCount} tests
                  </p>
                </div>
              </div>
            )}

            {importError && <p className="text-sm text-red-500 mb-4">{importError}</p>}

            <div className="flex justify-end gap-2">
              <button onClick={onClose} className="rounded border border-gray-300 px-4 py-2 text-sm hover:bg-gray-100">Cancel</button>
              <button
                onClick={() => void handleImport()}
                disabled={!parsedData || importing}
                className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {importing ? "Importing..." : "Import"}
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="rounded border border-green-200 bg-green-50 p-4 mb-4">
              <p className="text-sm text-green-800 font-medium">Import successful!</p>
              <p className="text-sm text-green-700 mt-1">
                Created {result.form_number} ({result.jurisdiction}) TY{result.tax_year} v{result.version}
                {result.existing_version != null && (
                  <span className="text-yellow-700"> (previous version: v{result.existing_version})</span>
                )}
              </p>
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={onClose} className="rounded border border-gray-300 px-4 py-2 text-sm hover:bg-gray-100">Close</button>
              <button
                onClick={() => { navigate(`/forms/${result.id}`); onClose(); }}
                className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                Open Form
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
/* eslint-enable @typescript-eslint/no-explicit-any */
