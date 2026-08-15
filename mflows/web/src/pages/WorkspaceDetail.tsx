import { useState, useRef } from "react";
import { Link, useParams } from "react-router-dom";
import {
  useGetWorkspaceQuery,
  useGetWorkspaceOverviewQuery,
  useGetWorkspaceDocumentsQuery,
  useGetWorkspaceBusinessRulesQuery,
  useGetWorkspaceActionsQuery,
  useGetWorkspaceWorkflowsQuery,
  useGetWorkspaceSynthesisQuery,
  useSynthesizeWorkspaceWorkflowMutation,
  useUploadBRDMutation,
} from "@/store/api";
import { Tabs } from "@/components/shared/Tabs";
import {
  FolderKanban,
  AlertTriangle,
  FileText,
  Wand2,
  Zap,
  ScrollText,
  Sparkles,
  GitBranch,
  Upload,
} from "lucide-react";

type TabKey =
  | "overview"
  | "documents"
  | "rules"
  | "actions"
  | "triggers"
  | "workflows";

const TABS: { label: string; value: TabKey }[] = [
  { label: "Overview", value: "overview" },
  { label: "Documents", value: "documents" },
  { label: "Business Rules", value: "rules" },
  { label: "Actions", value: "actions" },
  { label: "Triggers", value: "triggers" },
  { label: "Workflows", value: "workflows" },
];

const WorkspaceDetail = () => {
  const { id } = useParams();
  const wsId = Number(id);
  const [tab, setTab] = useState<TabKey>("overview");

  const { data: workspace } = useGetWorkspaceQuery(wsId);
  const { data: overview } = useGetWorkspaceOverviewQuery(wsId);

  if (!workspace) return <div className="h-6 w-40 rounded skeleton mt-8" />;

  return (
    <div className="animate-in space-y-5">
      <div className="flex items-center gap-2">
        <FolderKanban size={18} className="text-brand-600" />
        <div>
          <h1 className="text-xl font-semibold text-gray-900">{workspace.display_name}</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {workspace.name}
            {workspace.organization_name ? ` · ${workspace.organization_name}` : ""}
            {overview?.domain ? ` · ${overview.domain}` : ""}
          </p>
        </div>
        {overview?.status && (
          <span className="ml-auto text-2xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 capitalize">
            {overview.status}
          </span>
        )}
      </div>

      <Tabs value={tab} onChange={setTab} tabs={TABS} />

      {tab === "overview" && <OverviewTab wsId={wsId} overview={overview} />}
      {tab === "documents" && <DocumentsTab wsId={wsId} />}
      {tab === "rules" && <RulesTab wsId={wsId} />}
      {tab === "actions" && <ActionsTab wsId={wsId} />}
      {tab === "triggers" && <TriggersTab wsId={wsId} />}
      {tab === "workflows" && <WorkflowsTab wsId={wsId} />}
    </div>
  );
};

// ── Overview ──────────────────────────────────────────────────────────────────

const OverviewTab = ({ wsId, overview }: { wsId: number; overview: any }) => {
  const { data: synthesis } = useGetWorkspaceSynthesisQuery(wsId);
  const [synthesize, { data: synthResult, isLoading: synthesizing, error: synthError }] =
    useSynthesizeWorkspaceWorkflowMutation();
  const [wfName, setWfName] = useState("");
  const [domain, setDomain] = useState("finance");
  const synthErrorMsg = (synthError as any)?.data?.detail || "";

  if (!overview) return <div className="h-24 rounded skeleton" />;

  return (
    <div className="space-y-5">
      {overview.summary && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-1.5">Workspace summary</h3>
          <p className="text-sm text-gray-600">{overview.summary}</p>
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Stat label="BRDs" value={overview.brd_count} />
        <Stat label="Actions" value={overview.action_count} />
        <Stat label="Triggers" value={overview.trigger_count} />
        <Stat label="Business Rules" value={overview.business_rule_count} />
        <Stat label="Workflows" value={overview.workflow_count} />
        <Stat label="Generated Files" value={overview.generated_file_count} />
        <Stat label="Unresolved" value={overview.unresolved_action_count} danger={overview.unresolved_action_count > 0} />
        <Stat label="Review flags" value={overview.review_flag_count} danger={overview.review_flag_count > 0} />
      </div>

      {/* Two ways to build a workflow — deliberately distinct (see requirement 12). */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <Link to={`/workspaces/${wsId}/build`} className="card p-5 hover:border-brand-300 transition-colors block">
          <h3 className="text-sm font-semibold text-gray-900 mb-1 flex items-center gap-1.5">
            <Sparkles size={13} className="text-brand-600" /> Build with AI
          </h3>
          <p className="text-xs text-gray-500">
            Describe the workflow in your words. The AI uses this workspace's actions and business rules — not the global catalog.
          </p>
          <span className="inline-flex items-center gap-1 text-xs text-brand-600 mt-3 font-medium">
            Open builder →
          </span>
        </Link>

        <div className="card p-5 bg-gray-50/40">
          <h3 className="text-sm font-semibold text-gray-900 mb-1 flex items-center gap-1.5">
            <Wand2 size={13} className="text-gray-600" /> Synthesize from BRDs
          </h3>
          <p className="text-xs text-gray-500">
            Deterministic — chains all mapped workspace actions into one workflow. No AI. Use the form below.
          </p>
        </div>
      </div>

      {/* Deterministic synthesis form. */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-900 mb-1 flex items-center gap-1.5">
          <Wand2 size={13} className="text-brand-600" /> Synthesize from BRDs
        </h3>
        <p className="text-xs text-gray-500 mb-3">
          Deterministic — chains all mapped workspace actions into one workflow. No AI.
        </p>
        <div className="flex flex-wrap gap-2 items-end">
          <div className="flex-1 min-w-[160px]">
            <label className="text-2xs text-gray-500">Workflow name</label>
            <input className="input" value={wfName} onChange={(e) => setWfName(e.target.value)} placeholder="Combined Loan Workflow" />
          </div>
          <div className="min-w-[120px]">
            <label className="text-2xs text-gray-500">Domain</label>
            <select className="input" value={domain} onChange={(e) => setDomain(e.target.value)}>
              <option value="finance">finance</option>
            </select>
          </div>
          <button
            className="btn-brand disabled:opacity-50"
            disabled={synthesizing || !wfName || (overview.action_count || 0) === 0}
            onClick={() => synthesize({ workspaceId: wsId, name: wfName, domain })}
          >
            <Wand2 size={14} /> {synthesizing ? "Synthesizing..." : "Synthesize"}
          </button>
        </div>
        {synthErrorMsg && <p className="text-xs text-danger mt-2">{synthErrorMsg}</p>}
        {synthResult && (
          <p className="text-xs text-success font-medium mt-2">
            Created workflow #{synthResult.workflow_id} from {synthResult.brd_count} BRD(s) —{" "}
            <Link to={`/workflows/${synthResult.workflow_id}`} className="underline">
              view
            </Link>
          </p>
        )}
      </div>

      {(synthesis?.review_flags || []).length > 0 && (
        <div className="card p-5 border-amber-200 bg-amber-50/40">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-1.5">
            <AlertTriangle size={13} className="text-amber-600" /> Needs review
          </h3>
          <div className="space-y-1.5">
            {synthesis.review_flags.map((f: any, i: number) => (
              <div key={i} className="text-sm text-gray-700">
                {f.type === "low_confidence" && (
                  <span>Low confidence ({(f.min_confidence * 100).toFixed(0)}%) — <b>{f.action}</b></span>
                )}
                {f.type === "unresolved_action" && (
                  <span>Unresolved action — "<i>{f.term}</i>" from {f.source_document || "—"}</span>
                )}
                {f.type === "rule_conflict" && (
                  <span>Conflicting thresholds on "<i>{f.subject}</i>" across {f.rules?.length || 0} rules</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ── Documents ─────────────────────────────────────────────────────────────────

const DocumentsTab = ({ wsId }: { wsId: number }) => {
  const fileRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const { data, isLoading, refetch } = useGetWorkspaceDocumentsQuery(wsId);
  const [upload, { data: uploadResult, isLoading: uploading, error: uploadError }] = useUploadBRDMutation();
  const uploadErr = (uploadError as any)?.data?.detail || (uploadError ? "Upload failed" : "");

  function handleUpload() {
    if (!files.length) return;
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    fd.append("workspace_id", String(wsId));
    upload(fd).then(() => { setFiles([]); refetch(); });
  }

  if (isLoading) return <div className="h-24 rounded skeleton" />;
  const docs = data?.documents || [];

  return (
    <div className="space-y-3">
      {/* ── Upload BRDs ── */}
      <div className="card p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-1.5">
          <Upload size={13} className="text-brand-600" /> Upload BRDs
        </h3>
        <div
          onClick={() => fileRef.current?.click()}
          className="border-2 border-dashed border-gray-200 rounded-lg p-6 text-center cursor-pointer hover:border-brand-300 hover:bg-brand-50/20 transition-all group"
        >
          <Upload size={20} className="mx-auto text-gray-300 group-hover:text-brand-400 transition-colors mb-1" />
          <p className="text-sm text-gray-600">
            {files.length > 0 ? `${files.length} file(s) selected` : "Click to select PDFs"}
          </p>
          <p className="text-2xs text-gray-400 mt-0.5">Multiple PDFs allowed</p>
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
          <div className="mt-2 space-y-1">
            {files.map((f, i) => (
              <div key={i} className="flex items-center gap-2 text-xs text-gray-600">
                <FileText size={12} className="text-gray-400" />
                <span className="truncate">{f.name}</span>
              </div>
            ))}
            <button onClick={handleUpload} disabled={uploading} className="btn-brand mt-2 text-xs">
              <FileText size={13} /> {uploading ? "Processing..." : "Extract Knowledge"}
            </button>
          </div>
        )}
        {uploadErr && <p className="text-xs text-danger mt-2">{uploadErr}</p>}
        {uploadResult && (
          <p className="text-xs text-success font-medium mt-2">
            {uploadResult.succeeded}/{uploadResult.total} BRD(s) ingested successfully.
          </p>
        )}
      </div>

      {/* ── Uploaded documents ── */}
      {docs.length === 0 ? (
        <Empty text="No BRDs uploaded yet. Use the upload area above." />
      ) : (
        docs.map((d: any) => (
          <div key={d.workflow_knowledge_id} className="card p-4">
            <div className="flex items-center gap-2">
              <FileText size={14} className="text-brand-600 shrink-0" />
              <span className="font-medium text-gray-900 text-sm truncate">{d.name}</span>
              <MappingBadge status={d.mapping_status} />
              {d.uploaded_at && (
                <span className="text-2xs text-gray-400 ml-auto">
                  {new Date(d.uploaded_at).toLocaleDateString()}
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-x-5 gap-y-1 mt-2 text-2xs text-gray-500">
              <span>Extraction: <b className="text-gray-700">{d.extraction_status}</b></span>
              <span>Actions: <b className="text-gray-700">{d.mapped_action_count}/{d.action_count}</b> mapped</span>
              <span>Triggers: <b className="text-gray-700">{d.trigger_count}</b></span>
              <span>Business rules: <b className="text-gray-700">{d.business_rule_count}</b></span>
            </div>
          </div>
        ))
      )}
    </div>
  );
};

// ── Business Rules ──────────────────────────────────────────────────────────────

const RulesTab = ({ wsId }: { wsId: number }) => {
  const { data, isLoading } = useGetWorkspaceBusinessRulesQuery(wsId);
  if (isLoading) return <div className="h-24 rounded skeleton" />;
  const rules = data?.business_rules || [];
  const conflicts = data?.conflicts || [];

  if (rules.length === 0)
    return <Empty text="No business rules extracted yet." />;

  return (
    <div className="space-y-4">
    {conflicts.length > 0 && (
      <div className="card p-5 border-amber-300 bg-amber-50/60">
        <h3 className="text-sm font-semibold text-amber-800 mb-2 flex items-center gap-1.5">
          <AlertTriangle size={13} className="text-amber-600" /> Potential conflicts
        </h3>
        <div className="space-y-2">
          {conflicts.map((c: any, i: number) => (
            <div key={i} className="text-xs text-gray-700">
              <p className="font-medium text-gray-800">On "{c.subject}":</p>
              <ul className="mt-0.5 space-y-0.5">
                {c.rules.map((r: any, j: number) => (
                  <li key={j}>
                    <span className="text-gray-400">{r.source_document || "—"}:</span>{" "}
                    <span className="italic">"{r.rule}"</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    )}
    <div className="card p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-1.5">
        <ScrollText size={13} className="text-brand-600" /> Business rules MFlows extracted
      </h3>
      <ol className="space-y-2 list-none">
        {rules.map((r: any, i: number) => (
          <li key={i} className="flex items-start gap-2 text-sm">
            <span className="w-5 h-5 rounded bg-gray-100 text-gray-600 flex items-center justify-center text-2xs font-bold shrink-0">
              {i + 1}
            </span>
            <div className="min-w-0">
              <p className="text-gray-800">{r.rule}</p>
              {r.source_document && (
                <p className="text-2xs text-gray-400 mt-0.5">from {r.source_document}</p>
              )}
            </div>
          </li>
        ))}
      </ol>
    </div>
    </div>
  );
};

// ── Actions ─────────────────────────────────────────────────────────────────────

const ActionsTab = ({ wsId }: { wsId: number }) => {
  const { data, isLoading } = useGetWorkspaceActionsQuery(wsId);
  if (isLoading) return <div className="h-24 rounded skeleton" />;
  const actions = data?.actions || [];
  const unresolved = data?.unresolved_actions || [];

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">
          Workspace actions (deduplicated across BRDs)
        </h3>
        <p className="text-2xs text-gray-400 mb-3">
          These are the actions relevant to this workspace — the candidate set for generation. The full global catalog is available separately.
        </p>
        <div className="space-y-2">
          {actions.map((a: any) => (
            <div key={a.canonical_id} className="border-b border-gray-100 last:border-0 pb-2">
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-800 text-sm">{a.display_name}</span>
                <span className="text-2xs px-1.5 py-0.5 rounded bg-brand-50 text-brand-700">
                  {a.contributed_by} BRD{a.contributed_by > 1 ? "s" : ""}
                </span>
                {a.min_confidence != null && (
                  <span className="text-2xs text-gray-400 ml-auto">
                    min conf {(a.min_confidence * 100).toFixed(0)}%
                  </span>
                )}
              </div>
              <div className="mt-1 space-y-0.5">
                {(a.sources || []).map((s: any, i: number) => (
                  <p key={i} className="text-xs text-gray-500 flex items-center gap-1">
                    <FileText size={11} className="text-gray-300" />
                    <span className="text-gray-400">{s.source_document || "—"}:</span>{" "}
                    <span className="italic">"{s.clause}"</span>
                  </p>
                ))}
              </div>
            </div>
          ))}
          {actions.length === 0 && (
            <p className="text-sm text-gray-400">No mapped actions yet. Upload BRDs to this workspace.</p>
          )}
        </div>
      </div>

      {unresolved.length > 0 && (
        <div className="card p-5 border-amber-200 bg-amber-50/40">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-1.5">
            <AlertTriangle size={13} className="text-amber-600" /> Unresolved (no catalog match)
          </h3>
          <div className="space-y-1">
            {unresolved.map((u: any, i: number) => (
              <p key={i} className="text-sm text-gray-700">
                "<i>{u.term}</i>" <span className="text-2xs text-gray-400">from {u.source_document || "—"}</span>
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ── Triggers ──────────────────────────────────────────────────────────────────

const TriggersTab = ({ wsId }: { wsId: number }) => {
  const { data, isLoading } = useGetWorkspaceActionsQuery(wsId);
  if (isLoading) return <div className="h-24 rounded skeleton" />;
  const triggers = data?.triggers || [];

  if (triggers.length === 0)
    return <Empty text="No triggers mapped in this workspace yet." />;

  return (
    <div className="card p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-1.5">
        <Zap size={13} className="text-brand-600" /> Workspace triggers
      </h3>
      <div className="space-y-2">
        {triggers.map((t: any) => (
          <div key={t.canonical_id} className="border-b border-gray-100 last:border-0 pb-2">
            <span className="font-medium text-gray-800 text-sm">{t.trigger}</span>
            <div className="mt-1 space-y-0.5">
              {(t.sources || []).map((s: any, i: number) => (
                <p key={i} className="text-xs text-gray-500 flex items-center gap-1">
                  <FileText size={11} className="text-gray-300" />
                  <span className="text-gray-400">{s.source_document || "—"}:</span>{" "}
                  <span className="italic">"{s.clause}"</span>
                </p>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ── Workflows ─────────────────────────────────────────────────────────────────

const WorkflowsTab = ({ wsId }: { wsId: number }) => {
  const { data, isLoading } = useGetWorkspaceWorkflowsQuery(wsId);
  if (isLoading) return <div className="h-24 rounded skeleton" />;
  const workflows = data || [];

  if (workflows.length === 0)
    return <Empty text="No workflows generated in this workspace yet. Use Build with AI or Synthesize from BRDs." />;

  return (
    <div className="space-y-2">
      {workflows.map((w: any) => (
        <Link
          key={w.id}
          to={`/workflows/${w.id}`}
          className="card p-4 flex items-center gap-3 hover:border-brand-300 transition-colors"
        >
          <GitBranch size={15} className="text-brand-600 shrink-0" />
          <div className="min-w-0">
            <p className="font-medium text-gray-900 text-sm truncate">{w.name}</p>
            <p className="text-2xs text-gray-400">
              #{w.id} · {w.domain}
              {w.parsed_rule_json?.steps ? ` · ${w.parsed_rule_json.steps.length} step(s)` : ""}
            </p>
          </div>
          {w.status && (
            <span className="ml-auto text-2xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 capitalize">
              {w.status}
            </span>
          )}
        </Link>
      ))}
    </div>
  );
};

// ── shared bits ─────────────────────────────────────────────────────────────────

const Stat = ({ label, value, danger }: { label: string; value: any; danger?: boolean }) => (
  <div className="card p-4">
    <p className="text-2xs font-medium text-gray-500 mb-1">{label}</p>
    <p className={"text-sm font-semibold " + (danger ? "text-danger" : "text-gray-900")}>{value ?? 0}</p>
  </div>
);

const Empty = ({ text }: { text: string }) => (
  <div className="card p-8 text-center text-sm text-gray-400">{text}</div>
);

const MappingBadge = ({ status }: { status: string }) => {
  const map: Record<string, string> = {
    mapped: "bg-emerald-50 text-emerald-700",
    partial: "bg-amber-50 text-amber-700",
    unmapped: "bg-red-50 text-red-700",
    none: "bg-gray-100 text-gray-500",
  };
  return (
    <span className={"text-2xs px-1.5 py-0.5 rounded capitalize " + (map[status] || map.none)}>
      {status}
    </span>
  );
};

export default WorkspaceDetail;
