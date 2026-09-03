import { useState, useRef } from "react";
import { Link, useParams } from "react-router-dom";
import {
  useGetWorkspaceQuery,
  useGetWorkspaceOverviewQuery,
  useGetWorkspaceDocumentsQuery,
  useGetWorkspaceWorkflowsQuery,
  useGetUnmappedActionsQuery,
  useGetActionSuggestionsQuery,
  useResolveUnmappedActionMutation,
  useGetChainsQuery,
  useDetectChainsMutation,
  useUpdateChainMutation,
  useUploadBRDMutation,
  useGetWorkspaceBusinessRulesQuery,
  useGetWorkspaceDiagnosticsQuery,
} from "@/store/api";
import {
  FolderKanban, FileText, Upload, GitBranch, Sparkles,
  AlertTriangle, ChevronDown, ChevronRight, Check, X,
  Link2, RefreshCw, Search, Plus, ScrollText,
} from "lucide-react";
import { clsx } from "clsx";

// ── Main page ─────────────────────────────────────────────────────────────────
const WorkspaceDetail = () => {
  const { id } = useParams();
  const wsId = Number(id);
  const { data: workspace } = useGetWorkspaceQuery(wsId);
  const { data: overview } = useGetWorkspaceOverviewQuery(wsId);

  if (!workspace) return <div className="h-8 w-48 rounded skeleton mt-8" />;

  return (
    <div className="animate-in space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gray-100 flex items-center justify-center shrink-0">
          <FolderKanban size={16} className="text-gray-600" />
        </div>
        <div>
          <h1 className="text-xl font-semibold text-gray-900">{workspace.display_name}</h1>
          <p className="text-sm text-gray-400">
            {workspace.organization_name || workspace.name}
            {overview?.domain ? ` · ${overview.domain}` : ""}
          </p>
        </div>
        <Link
          to={`/workspaces/${wsId}/build`}
          className="ml-auto inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-900 text-white text-xs font-medium hover:bg-gray-700 transition-colors"
        >
          <Sparkles size={12} /> Build workflow
        </Link>
      </div>

      {/* Stats row */}
      {overview && (
        <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
          <StatPill label="BRDs"      value={overview.brd_count} />
          <StatPill label="Actions"   value={overview.action_count} />
          <StatPill label="Triggers"  value={overview.trigger_count} />
          <StatPill label="Rules"     value={overview.business_rule_count} />
          <StatPill label="Workflows" value={overview.workflow_count} />
          <StatPill label="Unresolved" value={overview.unresolved_action_count} warn={overview.unresolved_action_count > 0} />
          <StatPill label="Flags"     value={overview.review_flag_count} warn={overview.review_flag_count > 0} />
          <StatPill label="Files"     value={overview.generated_file_count} />
        </div>
      )}

      {/* Documents */}
      <DocumentsSection wsId={wsId} />

      {/* Unmapped actions — only shown when there are some */}
      <UnmappedActionsSection wsId={wsId} />

      {/* Workflows */}
      <WorkflowsSection wsId={wsId} />

      {/* Chains */}
      <ChainsSection wsId={wsId} />

      {/* Business rules — collapsible */}
      <CollapsibleSection title="Business rules" icon={<ScrollText size={14} className="text-gray-500" />}>
        <BusinessRulesContent wsId={wsId} />
      </CollapsibleSection>

      {/* Diagnostics — collapsible */}
      <CollapsibleSection title="Mapping diagnostics" icon={<Search size={14} className="text-gray-500" />}>
        <DiagnosticsContent wsId={wsId} />
      </CollapsibleSection>
    </div>
  );
};

// ── Documents ─────────────────────────────────────────────────────────────────
const DocumentsSection = ({ wsId }: { wsId: number }) => {
  const fileRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const { data, isLoading, refetch } = useGetWorkspaceDocumentsQuery(wsId);
  const [upload, { data: uploadResult, isLoading: uploading, error: uploadError }] = useUploadBRDMutation();
  const uploadErr = (uploadError as any)?.data?.detail || (uploadError ? "Upload failed" : "");
  const docs = data?.documents || [];

  function handleUpload() {
    if (!files.length) return;
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    fd.append("workspace_id", String(wsId));
    upload(fd).then(() => { setFiles([]); refetch(); });
  }

  return (
    <Section title="BRD Documents" icon={<FileText size={14} className="text-gray-500" />}>
      {/* Upload area */}
      <div
        onClick={() => fileRef.current?.click()}
        className="border-2 border-dashed border-gray-200 rounded-lg px-4 py-5 text-center cursor-pointer hover:border-gray-300 hover:bg-gray-50 transition-all"
      >
        <Upload size={18} className="mx-auto text-gray-300 mb-1.5" />
        <p className="text-sm text-gray-500">
          {files.length > 0 ? `${files.length} file(s) ready` : "Click to select PDFs"}
        </p>
        <p className="text-xs text-gray-400 mt-0.5">Multiple PDFs supported</p>
        <input ref={fileRef} type="file" accept=".pdf" multiple className="hidden"
          onChange={(e) => setFiles(Array.from(e.target.files || []))} />
      </div>

      {files.length > 0 && (
        <div className="mt-2 space-y-1">
          {files.map((f, i) => (
            <div key={i} className="flex items-center gap-2 text-xs text-gray-600">
              <FileText size={11} className="text-gray-400" />
              <span className="truncate">{f.name}</span>
            </div>
          ))}
          <button onClick={handleUpload} disabled={uploading}
            className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-900 text-white text-xs font-medium disabled:opacity-50">
            {uploading ? "Processing…" : "Extract Knowledge"}
          </button>
        </div>
      )}
      {uploadErr && <p className="text-xs text-red-500 mt-1.5">{uploadErr}</p>}
      {uploadResult && (
        <p className="text-xs text-emerald-600 font-medium mt-1.5">
          {uploadResult.succeeded}/{uploadResult.total} ingested successfully
        </p>
      )}

      {/* Doc list */}
      {!isLoading && docs.length > 0 && (
        <div className="mt-3 space-y-1.5">
          {docs.map((d: any) => (
            <div key={d.workflow_knowledge_id}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg border border-gray-100 bg-white">
              <FileText size={13} className="text-gray-400 shrink-0" />
              <span className="text-sm font-medium text-gray-800 flex-1 truncate">{d.name}</span>
              <MappingBadge status={d.mapping_status} />
              <span className="text-xs text-gray-400 tabular-nums">
                {d.mapped_action_count}/{d.action_count} actions
              </span>
            </div>
          ))}
        </div>
      )}
      {!isLoading && docs.length === 0 && (
        <p className="text-sm text-gray-400 mt-3">No BRDs uploaded yet.</p>
      )}
    </Section>
  );
};

// ── Unmapped actions ──────────────────────────────────────────────────────────
const UnmappedActionsSection = ({ wsId }: { wsId: number }) => {
  const { data, isLoading, refetch } = useGetUnmappedActionsQuery(wsId);
  const items: any[] = data?.unmapped_actions || [];
  if (isLoading || items.length === 0) return null;

  return (
    <Section
      title={`Unresolved actions (${items.length})`}
      icon={<AlertTriangle size={14} className="text-amber-500" />}
      headerExtra={
        <span className="text-xs text-amber-600 font-medium">
          These actions from your BRDs couldn't be matched automatically
        </span>
      }
    >
      <div className="space-y-2">
        {items.map((item: any) => (
          <UnmappedActionRow key={item.mapping_id} item={item} wsId={wsId} onResolved={refetch} />
        ))}
      </div>
    </Section>
  );
};

const UnmappedActionRow = ({ item, wsId, onResolved }: { item: any; wsId: number; onResolved: () => void }) => {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"catalog" | "custom">("catalog");
  const [selectedAdId, setSelectedAdId] = useState<number | null>(null);
  const [actionName, setActionName] = useState(
    item.extract_name.toLowerCase().replace(/\s+/g, "_")
  );
  const [displayName, setDisplayName] = useState(item.extract_name);
  const [executionType, setExecutionType] = useState("python");
  const [handler, setHandler] = useState(actionName);

  const { data: suggestions, isFetching: loadingSuggestions } =
    useGetActionSuggestionsQuery({ workspaceId: wsId, mappingId: item.mapping_id }, { skip: !open });
  const [resolve, { isLoading: resolving }] = useResolveUnmappedActionMutation();

  async function handleResolve() {
    if (mode === "catalog" && selectedAdId) {
      await resolve({ workspaceId: wsId, mappingId: item.mapping_id, action_definition_id: selectedAdId });
    } else if (mode === "custom") {
      await resolve({
        workspaceId: wsId,
        mappingId: item.mapping_id,
        action_name: actionName,
        display_name: displayName,
        execution_template: { execution_type: executionType, configuration: { handler } },
      });
    }
    onResolved();
  }

  return (
    <div className="rounded-lg border border-amber-100 bg-amber-50/30 overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center gap-2.5 px-3 py-2.5 text-left hover:bg-amber-50/60 transition-colors"
      >
        {open ? <ChevronDown size={13} className="text-gray-400 shrink-0" /> : <ChevronRight size={13} className="text-gray-400 shrink-0" />}
        <span className="text-sm font-medium text-gray-800 flex-1 truncate">"{item.extract_name}"</span>
        <span className="text-xs text-gray-400 truncate max-w-[180px]">{item.source_document}</span>
        <span className="text-xs text-amber-600">unresolved</span>
      </button>

      {open && (
        <div className="px-4 pb-4 pt-1 border-t border-amber-100 space-y-3">
          {item.description && (
            <p className="text-xs text-gray-500 italic">"{item.description}"</p>
          )}

          {/* Mode toggle */}
          <div className="flex gap-2">
            <button onClick={() => setMode("catalog")}
              className={clsx("px-2.5 py-1 rounded text-xs font-medium transition-colors",
                mode === "catalog" ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200")}>
              Map to catalog
            </button>
            <button onClick={() => setMode("custom")}
              className={clsx("px-2.5 py-1 rounded text-xs font-medium transition-colors",
                mode === "custom" ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200")}>
              Define custom
            </button>
          </div>

          {mode === "catalog" && (
            <div className="space-y-2">
              <p className="text-xs text-gray-500">Select from catalog suggestions:</p>
              {loadingSuggestions && <p className="text-xs text-gray-400">Loading suggestions…</p>}
              <div className="space-y-1">
                {(suggestions?.suggestions || []).map((s: any) => (
                  <button key={s.action_definition_id}
                    onClick={() => setSelectedAdId(s.action_definition_id)}
                    className={clsx("w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-xs border transition-colors",
                      selectedAdId === s.action_definition_id
                        ? "border-gray-900 bg-gray-50"
                        : "border-gray-100 hover:border-gray-200 hover:bg-gray-50/50"
                    )}>
                    <div className="flex-1 min-w-0">
                      <span className="font-medium text-gray-800">{s.display_name}</span>
                      <code className="ml-2 text-gray-400">{s.name}</code>
                    </div>
                    <span className="text-gray-400 tabular-nums">{(s.rank * 100).toFixed(0)}%</span>
                    {selectedAdId === s.action_definition_id && <Check size={12} className="text-gray-900 shrink-0" />}
                  </button>
                ))}
                {!loadingSuggestions && (suggestions?.suggestions || []).length === 0 && (
                  <p className="text-xs text-gray-400">No close matches found. Try defining custom.</p>
                )}
              </div>
            </div>
          )}

          {mode === "custom" && (
            <div className="space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs text-gray-500">Action name (handler key)</label>
                  <input className="input text-xs mt-0.5" value={actionName}
                    onChange={(e) => { setActionName(e.target.value); setHandler(e.target.value); }} />
                </div>
                <div>
                  <label className="text-xs text-gray-500">Display name</label>
                  <input className="input text-xs mt-0.5" value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs text-gray-500">Execution type</label>
                  <select className="input text-xs mt-0.5" value={executionType} onChange={(e) => setExecutionType(e.target.value)}>
                    <option value="python">python</option>
                    <option value="http">http</option>
                    <option value="human_task">human_task</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-500">Handler name</label>
                  <input className="input text-xs mt-0.5" value={handler} onChange={(e) => setHandler(e.target.value)} />
                </div>
              </div>
            </div>
          )}

          <button
            onClick={handleResolve}
            disabled={resolving || (mode === "catalog" && !selectedAdId)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-900 text-white text-xs font-medium disabled:opacity-40"
          >
            <Check size={12} /> {resolving ? "Saving…" : "Resolve action"}
          </button>
        </div>
      )}
    </div>
  );
};

// ── Workflows ─────────────────────────────────────────────────────────────────
const WorkflowsSection = ({ wsId }: { wsId: number }) => {
  const { data: workflows, isLoading } = useGetWorkspaceWorkflowsQuery(wsId);
  const list: any[] = workflows || [];

  return (
    <Section
      title="Workflows"
      icon={<GitBranch size={14} className="text-gray-500" />}
      headerExtra={
        <div className="flex items-center gap-2 ml-auto">
          <Link to={`/workspaces/${wsId}/build`}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-gray-900 text-white text-xs font-medium hover:bg-gray-700 transition-colors">
            <Sparkles size={11} /> AI build
          </Link>
        </div>
      }
    >
      {isLoading && <div className="h-12 rounded skeleton" />}
      {!isLoading && list.length === 0 && (
        <p className="text-sm text-gray-400">No workflows yet. Use AI build or synthesize from BRDs.</p>
      )}
      <div className="space-y-1.5 mt-1">
        {list.map((w: any) => (
          <Link key={w.id} to={`/workflows/${w.id}`}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg border border-gray-100 bg-white hover:border-gray-200 transition-colors">
            <GitBranch size={13} className="text-gray-400 shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800 truncate">{w.name}</p>
              <p className="text-xs text-gray-400">
                #{w.id} · {w.domain}
                {w.parsed_rule_json?.steps ? ` · ${w.parsed_rule_json.steps.length} steps` : ""}
              </p>
            </div>
            <span className={clsx("text-xs px-2 py-0.5 rounded-full capitalize",
              w.status === "active" ? "bg-emerald-50 text-emerald-700" : "bg-gray-100 text-gray-500")}>
              {w.status}
            </span>
          </Link>
        ))}
      </div>
    </Section>
  );
};

// ── Chains ────────────────────────────────────────────────────────────────────
const ChainsSection = ({ wsId }: { wsId: number }) => {
  const { data: chains = [], isLoading, refetch } = useGetChainsQuery({ workspaceId: wsId });
  const [detect, { isLoading: detecting }] = useDetectChainsMutation();
  const [update] = useUpdateChainMutation();

  if (!isLoading && chains.length === 0 && !detecting) {
    return (
      <Section title="Workflow chains" icon={<Link2 size={14} className="text-gray-500" />}
        headerExtra={
          <button onClick={() => detect(wsId).then(() => refetch())}
            className="ml-auto text-xs text-gray-500 hover:text-gray-800 inline-flex items-center gap-1 transition-colors">
            <RefreshCw size={11} /> Detect
          </button>
        }>
        <p className="text-sm text-gray-400">No chains detected yet. Click Detect to run analysis.</p>
      </Section>
    );
  }

  return (
    <Section title={`Workflow chains (${chains.length})`} icon={<Link2 size={14} className="text-gray-500" />}
      headerExtra={
        <button onClick={() => detect(wsId).then(() => refetch())} disabled={detecting}
          className="ml-auto text-xs text-gray-500 hover:text-gray-800 inline-flex items-center gap-1 disabled:opacity-40 transition-colors">
          <RefreshCw size={11} className={detecting ? "animate-spin" : ""} /> {detecting ? "Detecting…" : "Re-detect"}
        </button>
      }>
      {isLoading && <div className="h-16 rounded skeleton" />}
      <div className="space-y-2 mt-1">
        {chains.map((c: any) => (
          <ChainRow key={c.id} chain={c} wsId={wsId}
            onAccept={() => update({ workspaceId: wsId, chainId: c.id, status: "accepted" }).then(() => refetch())}
            onReject={() => update({ workspaceId: wsId, chainId: c.id, status: "rejected" }).then(() => refetch())}
          />
        ))}
      </div>
    </Section>
  );
};

const ChainRow = ({ chain, wsId, onAccept, onReject }: { chain: any; wsId: number; onAccept: () => void; onReject: () => void }) => {
  const statusColors: Record<string, string> = {
    auto:      "bg-emerald-50 text-emerald-700",
    accepted:  "bg-blue-50 text-blue-700",
    rejected:  "bg-gray-100 text-gray-400 line-through",
    suggested: "bg-amber-50 text-amber-700",
  };

  return (
    <div className={clsx("flex items-center gap-3 px-3 py-2.5 rounded-lg border text-sm",
      chain.status === "rejected" ? "border-gray-100 opacity-50" : "border-gray-100 bg-white")}>
      <Link2 size={13} className="text-gray-400 shrink-0" />
      <div className="flex-1 min-w-0">
        <span className="font-medium text-gray-700">{chain.source_action}</span>
        <span className="text-gray-400 mx-1.5">→</span>
        <span className="font-medium text-gray-700">{chain.target_trigger}</span>
        <span className="ml-2 text-xs text-gray-400">
          ({(chain.confidence * 100).toFixed(0)}% · {chain.match_type})
        </span>
      </div>
      <span className={clsx("text-xs px-2 py-0.5 rounded-full", statusColors[chain.status] || "bg-gray-100 text-gray-500")}>
        {chain.status}
      </span>
      {chain.status === "suggested" && (
        <div className="flex gap-1 shrink-0">
          <button onClick={onAccept} title="Accept"
            className="p-1 rounded hover:bg-emerald-50 text-emerald-600 transition-colors">
            <Check size={13} />
          </button>
          <button onClick={onReject} title="Reject"
            className="p-1 rounded hover:bg-red-50 text-red-400 transition-colors">
            <X size={13} />
          </button>
        </div>
      )}
    </div>
  );
};

// ── Business Rules (collapsible content) ─────────────────────────────────────
const BusinessRulesContent = ({ wsId }: { wsId: number }) => {
  const { data, isLoading } = useGetWorkspaceBusinessRulesQuery(wsId);
  if (isLoading) return <div className="h-12 rounded skeleton" />;
  const rules = data?.business_rules || [];
  if (!rules.length) return <p className="text-sm text-gray-400">No rules extracted yet.</p>;

  return (
    <ol className="space-y-2">
      {rules.map((r: any, i: number) => (
        <li key={i} className="flex items-start gap-2 text-sm">
          <span className="w-5 h-5 rounded bg-gray-100 text-gray-500 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
            {i + 1}
          </span>
          <div>
            <p className="text-gray-700">{r.rule}</p>
            {r.source_document && <p className="text-xs text-gray-400 mt-0.5">{r.source_document}</p>}
          </div>
        </li>
      ))}
    </ol>
  );
};

// ── Diagnostics (collapsible content) ────────────────────────────────────────
const DiagnosticsContent = ({ wsId }: { wsId: number }) => {
  const { data, isLoading } = useGetWorkspaceDiagnosticsQuery(wsId);
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});
  if (isLoading) return <div className="h-16 rounded skeleton" />;
  if (!data) return <p className="text-sm text-gray-400">No diagnostic data.</p>;

  const { totals, brds } = data;

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="grid grid-cols-6 gap-2 text-center">
        {[
          ["Extracted", totals.extracted_actions, ""],
          ["Mapped",    totals.mapped,             "text-emerald-600"],
          ["Unmapped",  totals.unmapped,            "text-red-500"],
          ["Miss",      totals.retrieval_miss,      "text-red-500"],
          ["Rejected",  totals.mapping_rejected,    "text-amber-600"],
          ["Pending",   totals.pending,             ""],
        ].map(([label, val, color]) => (
          <div key={label as string} className="rounded-lg border border-gray-100 py-2">
            <p className={clsx("text-sm font-bold", color || "text-gray-800")}>{val}</p>
            <p className="text-xs text-gray-400 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Per-BRD */}
      {(brds || []).map((brd: any) => (
        <div key={brd.workflow_knowledge_id}>
          <p className="text-xs font-semibold text-gray-500 mb-1.5">
            {brd.source_document || brd.workflow_name}
          </p>
          <div className="space-y-1">
            {brd.actions.map((a: any) => {
              const isOpen = !!expanded[a.mapping_id];
              const mapped = a.diagnostic === "MAPPED";
              return (
                <div key={a.mapping_id} className="rounded-lg border border-gray-100 overflow-hidden">
                  <button
                    onClick={() => setExpanded((e) => ({ ...e, [a.mapping_id]: !e[a.mapping_id] }))}
                    className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-gray-50 transition-colors"
                  >
                    <span className={mapped ? "text-emerald-500 text-xs" : "text-amber-500 text-xs"}>
                      {mapped ? "✓" : "⚠"}
                    </span>
                    <span className="text-sm text-gray-700 flex-1 truncate">{a.extract_name}</span>
                    {mapped && a.matched_action && (
                      <code className="text-xs text-gray-400 hidden sm:block">→ {a.matched_action.name}</code>
                    )}
                    {a.confidence != null && (
                      <span className="text-xs text-gray-400">{(a.confidence * 100).toFixed(0)}%</span>
                    )}
                    <span className="text-gray-300 text-xs">{isOpen ? "▲" : "▼"}</span>
                  </button>
                  {isOpen && (
                    <div className="px-3 pb-3 pt-1 border-t border-gray-100 bg-gray-50/40 space-y-2">
                      {a.query_text && (
                        <div>
                          <p className="text-xs text-gray-400 mb-0.5">Query</p>
                          <code className="text-xs text-gray-600 bg-white border border-gray-100 rounded px-1.5 py-0.5 block">{a.query_text}</code>
                        </div>
                      )}
                      {(a.top_candidates || []).length > 0 && (
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Top candidates</p>
                          {a.top_candidates.slice(0, 6).map((c: any, i: number) => (
                            <div key={i} className="flex items-center gap-2 text-xs py-0.5">
                              <span className="text-gray-400 w-4 text-right">{i + 1}.</span>
                              <span className="font-medium text-gray-700 flex-1 truncate">{c.display_name || c.name}</span>
                              {c.confidence != null && <span className="text-gray-400">{(c.confidence * 100).toFixed(0)}%</span>}
                              <span className="text-gray-300">rrf {c.rrf_score?.toFixed(3)}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};

// ── Shared primitives ─────────────────────────────────────────────────────────
const Section = ({
  title, icon, children, headerExtra,
}: {
  title: string; icon?: React.ReactNode; children: React.ReactNode; headerExtra?: React.ReactNode;
}) => (
  <div className="space-y-3">
    <div className="flex items-center gap-2">
      {icon}
      <h2 className="text-sm font-semibold text-gray-700">{title}</h2>
      {headerExtra}
    </div>
    {children}
  </div>
);

const CollapsibleSection = ({
  title, icon, children,
}: {
  title: string; icon?: React.ReactNode; children: React.ReactNode;
}) => {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center gap-2 py-1.5 text-left group"
      >
        {icon}
        <h2 className="text-sm font-semibold text-gray-500 group-hover:text-gray-700 transition-colors">{title}</h2>
        <span className="text-gray-300 text-xs ml-1">{open ? "▲" : "▼"}</span>
      </button>
      {open && <div className="mt-3">{children}</div>}
    </div>
  );
};

const StatPill = ({ label, value, warn }: { label: string; value: any; warn?: boolean }) => (
  <div className="rounded-lg border border-gray-100 bg-white px-3 py-2 text-center">
    <p className={clsx("text-sm font-bold", warn ? "text-amber-600" : "text-gray-800")}>{value ?? 0}</p>
    <p className="text-[10px] text-gray-400 mt-0.5 leading-none">{label}</p>
  </div>
);

const MappingBadge = ({ status }: { status: string }) => {
  const colors: Record<string, string> = {
    mapped:   "bg-emerald-50 text-emerald-700",
    partial:  "bg-amber-50 text-amber-700",
    unmapped: "bg-red-50 text-red-600",
    none:     "bg-gray-100 text-gray-400",
  };
  return (
    <span className={clsx("text-xs px-1.5 py-0.5 rounded capitalize", colors[status] || colors.none)}>
      {status}
    </span>
  );
};

export default WorkspaceDetail;
