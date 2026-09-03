import { useParams, Link } from "react-router-dom";
import {
  useGetExecutionQuery,
  usePauseExecutionMutation,
  useResumeExecutionMutation,
  useGetTracesQuery,
} from "@/store/api";
import StatusBadge from "@/components/StatusBadge";
import { Pause, Play, RefreshCw, Activity, ArrowLeft, GitBranch } from "lucide-react";
import { clsx } from "clsx";

const STATUS_COLOR: Record<string, string> = {
  completed: "border-emerald-400 bg-emerald-400",
  running:   "border-blue-400 bg-blue-400 animate-pulse",
  failed:    "border-red-400 bg-red-400",
  waiting:   "border-amber-400 bg-amber-400",
  blocked:   "border-amber-400 bg-amber-300",
  skipped:   "border-gray-300 bg-gray-200",
  pending:   "border-gray-300 bg-white",
};

const ExecutionDetail = () => {
  const { id } = useParams();
  const { data: exec, refetch, isLoading } = useGetExecutionQuery(id!, { pollingInterval: 4000 });
  const { data: tracesData } = useGetTracesQuery(
    { execution_id: id, page_size: 100 },
    { skip: !id }
  );
  const [pause]  = usePauseExecutionMutation();
  const [resume] = useResumeExecutionMutation();

  if (isLoading) return <div className="h-8 w-48 rounded skeleton mt-8" />;
  if (!exec)     return <div className="text-sm text-gray-400 mt-8">Execution not found.</div>;

  const traces: any[] = tracesData?.data || [];
  const steps: any[]  = exec.steps || [];

  return (
    <div className="animate-in space-y-5">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to="/executions" className="text-gray-400 hover:text-gray-600 transition-colors">
          <ArrowLeft size={16} />
        </Link>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-semibold text-gray-900">
            Execution #{exec.id}
          </h1>
          <p className="text-sm text-gray-400 mt-0.5">
            {exec.workflow_name || `Workflow #${exec.workflow_id}`}
            {exec.trace_id ? ` · ${exec.trace_id}` : ""}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <StatusBadge status={exec.status} />
          {exec.status === "RUNNING" && (
            <button onClick={() => pause(Number(exec.id))}
              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-gray-200 text-xs font-medium hover:bg-gray-50 transition-colors">
              <Pause size={12} /> Pause
            </button>
          )}
          {exec.status === "PAUSED" && (
            <button onClick={() => resume(Number(exec.id))}
              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-gray-900 text-white text-xs font-medium hover:bg-gray-700 transition-colors">
              <Play size={12} /> Resume
            </button>
          )}
          <button onClick={() => refetch()} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 transition-colors">
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat label="Duration"  value={exec.duration_ms ? `${(exec.duration_ms / 1000).toFixed(2)}s` : "—"} />
        <Stat label="Attempts"  value={exec.attempts ?? exec.retry_count ?? 0} />
        <Stat label="Entity"    value={exec.entity_id || "—"} />
        <Stat label="Error"     value={exec.last_error || exec.error || "none"} danger={!!(exec.last_error || exec.error)} />
      </div>

      {/* Step timeline */}
      {steps.length > 0 && (
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-gray-800 mb-4">Steps</h2>
          <div className="space-y-0">
            {steps.map((step: any, i: number) => (
              <div key={step.id ?? i} className="flex items-start gap-3 relative pl-5 pb-4 last:pb-0">
                {/* connector line */}
                {i < steps.length - 1 && (
                  <div className="absolute left-[9px] top-3.5 bottom-0 w-px bg-gray-200" />
                )}
                {/* dot */}
                <div className={clsx(
                  "absolute left-[3px] top-1 w-3.5 h-3.5 rounded-full border-2 bg-white",
                  STATUS_COLOR[step.status?.toLowerCase()] || "border-gray-300 bg-white"
                )} />
                <div className="flex-1 min-w-0 ml-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-gray-900 text-sm">{step.step_name || step.name || step.action}</span>
                    <StatusBadge status={step.status} />
                    {step.duration_ms != null && (
                      <span className="text-xs text-gray-400 font-mono">{step.duration_ms}ms</span>
                    )}
                    {step.step_id && (
                      <span className="text-xs text-gray-300 font-mono">id:{step.step_id}</span>
                    )}
                  </div>
                  {step.error && (
                    <p className="text-xs text-red-500 mt-1">{step.error}</p>
                  )}
                  {step.output_payload?.rule_evaluations && (
                    <p className="text-xs text-amber-600 mt-1">
                      Rule blocked: {step.output_payload.rule_evaluations.blocking_rule}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trace events */}
      {traces.length > 0 && (
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Activity size={14} className="text-gray-500" />
            Trace events ({traces.length})
          </h2>
          <TraceTimeline traces={traces} />
        </div>
      )}

      {/* Workflow link */}
      {exec.workflow_id && (
        <Link to={`/workflows/${exec.workflow_id}`}
          className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-700 transition-colors">
          <GitBranch size={13} /> View workflow #{exec.workflow_id}
        </Link>
      )}
    </div>
  );
};

// ── Trace timeline ────────────────────────────────────────────────────────────
const TraceTimeline = ({ traces }: { traces: any[] }) => {
  // Find time range for proportional bar widths
  const times = traces
    .map((t) => t.created_at ? new Date(t.created_at).getTime() : null)
    .filter(Boolean) as number[];
  const tMin = times.length ? Math.min(...times) : 0;
  const tMax = times.length ? Math.max(...times) : 1;
  const span = tMax - tMin || 1;

  const EVENT_COLORS: Record<string, string> = {
    WORKFLOW_STARTED:   "bg-blue-400",
    WORKFLOW_COMPLETED: "bg-emerald-400",
    WORKFLOW_FAILED:    "bg-red-400",
    STEP_STARTED:       "bg-blue-300",
    STEP_COMPLETED:     "bg-emerald-300",
    STEP_FAILED:        "bg-red-300",
    ACTION_DISPATCHED:  "bg-gray-300",
    ACTION_SUCCESS:     "bg-emerald-200",
    ACTION_FAILED:      "bg-red-200",
  };

  return (
    <div className="space-y-2">
      {/* Proportional timeline bar */}
      {times.length > 1 && (
        <div className="relative h-5 bg-gray-100 rounded-full overflow-hidden mb-4">
          {traces.map((t, i) => {
            if (!t.created_at) return null;
            const pos = ((new Date(t.created_at).getTime() - tMin) / span) * 100;
            const color = EVENT_COLORS[t.event_type] || "bg-gray-400";
            return (
              <div
                key={i}
                title={t.event_type}
                style={{ left: `${pos}%` }}
                className={clsx("absolute top-1 w-2 h-3 rounded-sm", color)}
              />
            );
          })}
        </div>
      )}

      {/* Event list */}
      <div className="space-y-1 max-h-64 overflow-y-auto">
        {traces.map((t: any, i: number) => (
          <div key={i} className="flex items-center gap-3 text-xs py-1 border-b border-gray-50 last:border-0">
            <div className={clsx(
              "w-2 h-2 rounded-full shrink-0",
              EVENT_COLORS[t.event_type] || "bg-gray-300"
            )} />
            <span className="font-mono text-gray-600 w-48 truncate shrink-0">{t.event_type}</span>
            <span className="text-gray-400 flex-1 truncate">{t.message || t.event_source || "—"}</span>
            <span className="text-gray-300 font-mono shrink-0">
              {t.created_at ? new Date(t.created_at).toLocaleTimeString() : ""}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

const Stat = ({ label, value, danger }: { label: string; value: any; danger?: boolean }) => (
  <div className="card p-4">
    <p className="text-xs text-gray-400 mb-1">{label}</p>
    <p className={clsx("text-sm font-semibold truncate", danger ? "text-red-500" : "text-gray-900")}>
      {value}
    </p>
  </div>
);

export default ExecutionDetail;
