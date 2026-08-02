import { useRef, useState } from "react";
import { useUploadBRDMutation } from "@/store/api";
import { Upload, FileText, CheckCircle2, XCircle } from "lucide-react";

export default function KnowledgeIngestion() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [upload, { data: result, isLoading, error }] = useUploadBRDMutation();

  const errorMsg = (error as any)?.data?.detail || (error ? "Upload failed" : "");

  function handleUpload() {
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    upload(form);
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">BRD Ingestion</h1>

      <div
        onClick={() => fileRef.current?.click()}
        className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center cursor-pointer hover:border-brand-400 hover:bg-brand-50/30 transition-colors"
      >
        <Upload className="mx-auto text-gray-400 mb-3" size={36} />
        <p className="text-sm text-gray-600 font-medium">{file ? file.name : "Click to upload a Banking BRD (PDF)"}</p>
        <p className="text-xs text-gray-400 mt-1">Only PDF files accepted</p>
        <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      </div>

      {file && (
        <button onClick={handleUpload} disabled={isLoading} className="mt-4 inline-flex items-center gap-2 px-5 py-2.5 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 disabled:opacity-50 transition-colors">
          <FileText size={16} />
          {isLoading ? "Processing..." : "Extract Workflow Knowledge"}
        </button>
      )}

      {errorMsg && <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{errorMsg}</div>}

      {result && (
        <div className="mt-6 space-y-4">
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
            <h3 className="font-semibold text-emerald-800">{result.workflow_name}</h3>
            <p className="text-sm text-emerald-700 mt-1">{result.summary}</p>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Actions</h4>
            <div className="space-y-1">
              {(result.action_references || []).map((a: any, i: number) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  {a.matched_action_definition_id ? <CheckCircle2 size={14} className="text-emerald-500" /> : <XCircle size={14} className="text-red-400" />}
                  <span className="text-gray-800">{a.name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
