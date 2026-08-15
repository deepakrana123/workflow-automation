import { useRef, useState } from "react";
import { useUploadBRDMutation, useGetWorkspacesQuery } from "@/store/api";
import { Upload, FileText, CheckCircle2, XCircle } from "lucide-react";

const KnowledgeIngestion = () => {
  const fileRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const { data: workspaces } = useGetWorkspacesQuery();
  const [workspaceId, setWorkspaceId] = useState<number | "">("");
  const [upload, { data: result, isLoading, error }] = useUploadBRDMutation();
  const errorMsg = (error as any)?.data?.detail || (error ? "Upload failed" : "");

  // Default to the first workspace once loaded.
  const effectiveWs = workspaceId || workspaces?.[0]?.id || "";

  function handleUpload() {
    if (files.length === 0 || !effectiveWs) return;
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    fd.append("workspace_id", String(effectiveWs));
    upload(fd);
  }

  return (
    <div className="animate-in space-y-5 max-w-xl">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">BRD Ingestion</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Upload one or more banking requirement documents into a workspace
        </p>
      </div>

      <div>
        <label className="text-2xs text-gray-500">Workspace</label>
        <select
          className="input"
          value={effectiveWs}
          onChange={(e) => setWorkspaceId(Number(e.target.value))}
        >
          {(workspaces || []).map((w: any) => (
            <option key={w.id} value={w.id}>
              {w.display_name}
            </option>
          ))}
        </select>
      </div>

      <div
        onClick={() => fileRef.current?.click()}
        className="card p-10 text-center cursor-pointer hover:border-brand-300 hover:bg-brand-50/30 transition-all group"
      >
        <Upload
          size={24}
          className="mx-auto text-gray-300 group-hover:text-brand-500 transition-colors mb-2"
        />
        <p className="text-sm font-medium text-gray-700">
          {files.length > 0 ? `${files.length} file(s) selected` : "Click to upload PDFs"}
        </p>
        <p className="text-2xs text-gray-400 mt-1">PDF files — multiple allowed</p>
        <input
          ref={fileRef}
          type="file"
          accept=".pdf"
          multiple
          className="hidden"
          onChange={(e) => setFiles(Array.from(e.target.files || []))}
        />
      </div>

      {files.length > 0 && (
        <div className="card p-3 space-y-1">
          {files.map((f, i) => (
            <div key={i} className="flex items-center gap-2 text-sm text-gray-700">
              <FileText size={13} className="text-gray-400" />
              <span className="truncate">{f.name}</span>
            </div>
          ))}
        </div>
      )}

      {files.length > 0 && (
        <button onClick={handleUpload} disabled={isLoading} className="btn-brand">
          <FileText size={14} /> {isLoading ? "Processing..." : "Extract Knowledge"}
        </button>
      )}

      {errorMsg && (
        <div className="card border-red-200 bg-red-50 p-3 text-sm text-danger">{errorMsg}</div>
      )}

      {result && (
        <div className="space-y-3 animate-in">
          <div className="card border-emerald-200 bg-emerald-50 p-4">
            <h3 className="font-semibold text-gray-900 text-sm">
              {result.succeeded}/{result.total} ingested
            </h3>
            {result.failed > 0 && (
              <p className="text-xs text-danger mt-1">{result.failed} failed</p>
            )}
          </div>
          <div className="card p-4">
            <h4 className="text-2xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
              Results
            </h4>
            <div className="space-y-1.5">
              {(result.results || []).map((r: any, i: number) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  {r.status === "success" ? (
                    <CheckCircle2 size={14} className="text-success" />
                  ) : (
                    <XCircle size={14} className="text-danger" />
                  )}
                  <span className="text-gray-800 truncate">{r.filename}</span>
                  <span className="text-2xs text-gray-400 ml-auto">
                    {r.status === "success" ? r.workflow_name : r.error}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeIngestion;
