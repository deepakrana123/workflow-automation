import { useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import {
  useGetWorkspaceQuery,
  useGetWorkspaceOverviewQuery,
  useGetWorkspaceBusinessRulesQuery,
  useGetActionsQuery,
  useGenerateWorkspaceWorkflowMutation,
} from "@/store/api";
import {
  Sparkles,
  ArrowLeft,
  Plus,
  X,
  Search,
  FolderKanban,
  ScrollText,
  AlertTriangle,
} from "lucide-react";

const WorkspaceBuildWorkflow = () => {
  const { id } = useParams();
  const wsId = Number(id);
  const navigate = useNavigate();

  const { data: workspace } = useGetWorkspaceQuery(wsId);
  const { data: overview } = useGetWorkspaceOverviewQuery(wsId);
  const { data: rulesData } = useGetWorkspaceBusinessRulesQuery(wsId);

  const [name, setName] = useState("");
  const [instruction, setInstruction] = useState("");
  const [selected, setSelected] = useState<any[]>([]);

  const [generate, { data: result, isLoading, error }] = useGenerateWorkspaceWorkflowMutation();
  const errorMsg = (error as any)?.data?.detail || (error ? "Generation failed" : "");

  const rules = rulesData?.business_rules || [];
  const conflicts = rulesData?.conflicts || [];

  const handleGenerate = () => {
    generate({
      workspaceId: wsId,
      name,
      user_request: instruction,
      selected_action_ids: selected.map((a) => a.id),
    });
  };

  if (!workspace) return <div className="h-6 w-40 rounded skeleton mt-8" />;

  return (
    <div className="animate-in space-y-5 max-w-2xl">
      <div>
        <Link to={`/workspaces/${wsId}`} className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 mb-1">
          <ArrowLeft size={12} /> {workspace.display_name}
        </Link>
        <h1 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
          <Sparkles size={18} className="text-brand-600" /> Build with AI
        </h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Generated from this workspace's context — not the global catalog.
        </p>
      </div>

      {/* A. Workspace context */}
      <div className="card p-4">
        <h3 className="text-2xs font-semibold text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1.5">
          <FolderKanban size={12} className="text-brand-600" /> Workspace context
        </h3>
        <div className="grid grid-cols-4 gap-2 text-center">
          <Ctx label="BRDs" value={overview?.brd_count} />
          <Ctx label="Actions" value={overview?.action_count} />
          <Ctx label="Triggers" value={overview?.trigger_count} />
          <Ctx label="Rules" value={overview?.business_rule_count} />
        </div>
        {overview?.summary && <p className="text-xs text-gray-600 mt-3">{overview.summary}</p>}
      </div>

      {conflicts.length > 0 && <ConflictBanner conflicts={conflicts} />}

      {/* C. Workspace knowledge — business rules */}
      {rules.length > 0 && (
        <div className="card p-4">
          <h3 className="text-2xs font-semibold text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1.5">
            <ScrollText size={12} className="text-brand-600" /> Business rules the AI will respect
          </h3>
          <ol className="space-y-1">
            {rules.map((r: any, i: number) => (
              <li key={i} className="text-xs text-gray-600">
                {i + 1}. {r.rule}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* B. Instruction + explicit action selection */}
      {!result && (
        <div className="card p-5 space-y-4">
          <div>
            <label className="text-2xs text-gray-500">Workflow name</label>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="personal_loan_approval_flow" />
          </div>
          <div>
            <label className="text-2xs text-gray-500">Instruction</label>
            <textarea
              className="input"
              rows={4}
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              placeholder="Create a workflow for processing a personal loan application after KYC verification."
            />
          </div>

          <ActionPicker selected={selected} setSelected={setSelected} />

          <button
            className="btn-brand disabled:opacity-50"
            disabled={isLoading || !name || !instruction}
            onClick={handleGenerate}
          >
            <Sparkles size={14} /> {isLoading ? "Generating..." : "Generate Workflow"}
          </button>
          {errorMsg && <p className="text-xs text-danger">{errorMsg}</p>}
        </div>
      )}

      {/* Review */}
      {result && <ReviewResult result={result} onBack={() => navigate(`/workspaces/${wsId}`)} />}
    </div>
  );
};

// ── Global action picker ─────────────────────────────────────────────────────

const ActionPicker = ({ selected, setSelected }: { selected: any[]; setSelected: (a: any[]) => void }) => {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const { data } = useGetActionsQuery({ page_size: 20, search }, { skip: !open || search.length < 2 });
  const results = data?.data || [];

  const add = (a: any) => {
    if (!selected.find((s) => s.id === a.id)) setSelected([...selected, a]);
  };
  const remove = (aid: number) => setSelected(selected.filter((s) => s.id !== aid));

  return (
    <div>
      <div className="flex items-center justify-between">
        <label className="text-2xs text-gray-500">Extra actions (optional — from the global catalog)</label>
        <button type="button" onClick={() => setOpen((o) => !o)} className="text-2xs text-brand-600 inline-flex items-center gap-1 hover:underline">
          <Plus size={12} /> Add Action
        </button>
      </div>

      {selected.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {selected.map((a) => (
            <span key={a.id} className="text-2xs px-2 py-0.5 rounded-full bg-brand-50 text-brand-700 inline-flex items-center gap-1">
              {a.display_name || a.name}
              <button type="button" onClick={() => remove(a.id)} className="hover:text-brand-900">
                <X size={10} />
              </button>
            </span>
          ))}
        </div>
      )}

      {open && (
        <div className="mt-2 border border-gray-200 rounded-lg p-2">
          <div className="relative">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              className="input pl-8"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search global actions (e.g. generate pdf, send email)..."
              autoFocus
            />
          </div>
          <div className="mt-2 max-h-52 overflow-y-auto space-y-0.5 scroll-thin">
            {search.length < 2 && <p className="text-2xs text-gray-400 px-1 py-1">Type at least 2 characters.</p>}
            {results.map((a: any) => {
              const already = !!selected.find((s) => s.id === a.id);
              return (
                <button
                  key={a.id}
                  type="button"
                  disabled={already}
                  onClick={() => add(a)}
                  className="w-full text-left px-2 py-1.5 rounded-md hover:bg-gray-50 disabled:opacity-40 flex items-center gap-2"
                >
                  <Plus size={12} className="text-brand-500 shrink-0" />
                  <span className="text-xs font-medium text-gray-800">{a.display_name}</span>
                  <code className="text-2xs text-gray-400 ml-auto">{a.name}</code>
                </button>
              );
            })}
            {search.length >= 2 && results.length === 0 && (
              <p className="text-2xs text-gray-400 px-1 py-1">No matches.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// ── Review ───────────────────────────────────────────────────────────────────

const ReviewResult = ({ result, onBack }: { result: any; onBack: () => void }) => (
  <div className="space-y-4 animate-in">
    <div className="card border-emerald-200 bg-emerald-50 p-3 text-sm text-success font-medium">
      <Sparkles size={14} className="inline mr-1" />
      Created workflow #{result.workflow_id} —{" "}
      <Link to={`/workflows/${result.workflow_id}`} className="underline">
        open
      </Link>
    </div>

    <div className="card p-4">
      <h3 className="text-2xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Workflow</h3>
      <div className="space-y-1.5">
        {result.parsed_rule_json?.steps?.map((step: any) => (
          <div key={step.id} className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg text-sm">
            <span className="w-5 h-5 rounded bg-brand-100 text-brand-700 flex items-center justify-center text-2xs font-bold">
              {step.id}
            </span>
            <span className="font-medium text-gray-800">{step.action}</span>
            {step.depends_on?.length > 0 && (
              <span className="text-2xs text-gray-400">→ {step.depends_on.join(", ")}</span>
            )}
          </div>
        ))}
      </div>
    </div>

    {result.dsl && (
      <div className="card p-4">
        <h3 className="text-2xs font-semibold text-gray-500 uppercase tracking-wide mb-2">DSL</h3>
        <pre className="text-xs font-mono text-gray-700 bg-gray-50 rounded-lg p-3 overflow-x-auto">{result.dsl}</pre>
      </div>
    )}

    {result.explanation && (
      <div className="card p-4">
        <h3 className="text-2xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Why this workflow</h3>
        <p className="text-sm text-gray-700 mb-3">{result.explanation.summary}</p>
        <div className="space-y-2">
          {(result.explanation.steps || []).map((s: any) => (
            <div key={s.id} className="flex items-start gap-2 text-sm">
              <span className="w-5 h-5 rounded bg-gray-100 text-gray-600 flex items-center justify-center text-2xs font-bold shrink-0">
                {s.id}
              </span>
              <div className="min-w-0">
                <span className="font-medium text-gray-800">{s.display_name}</span>
                <p className="text-xs text-gray-500">{s.explanation}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    )}

    <button onClick={onBack} className="inline-flex items-center gap-1 text-sm text-brand-600 hover:underline">
      <ArrowLeft size={13} /> Back to workspace
    </button>
  </div>
);

const ConflictBanner = ({ conflicts }: { conflicts: any[] }) => (
  <div className="card p-4 border-amber-300 bg-amber-50/60">
    <h3 className="text-sm font-semibold text-amber-800 mb-2 flex items-center gap-1.5">
      <AlertTriangle size={14} className="text-amber-600" /> Potential conflict — review recommended
    </h3>
    <p className="text-xs text-amber-800/80 mb-2">
      Different BRDs specify conflicting thresholds. MFlows will not silently choose one — review before generating.
    </p>
    <div className="space-y-2">
      {conflicts.map((c: any, i: number) => (
        <div key={i} className="text-xs text-gray-700">
          <p className="font-medium text-gray-800">On "{c.subject}":</p>
          <ul className="mt-0.5 space-y-0.5">
            {c.rules.map((r: any, j: number) => (
              <li key={j} className="flex items-start gap-1">
                <span className="text-gray-400">{r.source_document || "—"}:</span>
                <span className="italic">"{r.rule}"</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  </div>
);

const Ctx = ({ label, value }: { label: string; value: any }) => (
  <div>
    <p className="text-sm font-semibold text-gray-900">{value ?? 0}</p>
    <p className="text-2xs text-gray-500">{label}</p>
  </div>
);

export default WorkspaceBuildWorkflow;
