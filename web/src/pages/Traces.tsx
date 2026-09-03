import { useState } from "react";
import { Link } from "react-router-dom";
import { useGetTracesQuery } from "@/store/api";
import { Search, ChevronDown, ChevronRight, Activity, ExternalLink } from "lucide-react";
import { clsx } from "clsx";

const EVENT_DOT: Record<string, string> = {
  WORKFLOW_STARTED:   "bg-blue-400",
  WORKFLOW_COMPLETED: "bg-emerald-400",
  WORKFLOW_FAILED:    "bg-red-400",
  STEP_STARTED:       "bg-blue-300",
  STEP_COMPLETED:     "bg-emerald-300",
  STEP_FAILED:        "bg-red-300",
  ACTION_DISPATCHED:  "bg-gray-400",
  ACTION_SUCCESS:     "bg-emerald-200",
  ACTION_FAILED:      "bg-red-200",
};

const STATUS_PILL: Record<string, string> = {
  completed: "bg-emerald-50 text-emerald-700",
  failed:    "bg-red-50 text-red-600",
  running:   "bg-blue-50 text-blue-700",
  pending:   "bg-gray-100 text-gray-500",
};

const Traces = () => {
  const [page,        setPage]        = useState(1);
  const [executionId, setExecutionId] = useState("");
  const [statusFilter,setStatusFilter]= useState("");
  const [expanded,    setExpanded]    = useState<Set<string>>(new Set());

  const { data, isLoading, refetch } = useGetTracesQuery({
    page,
    page_size: 30,
    execution_id: executionId || undefined,
    status: statusFilter || undefined,
  });

  const traces: any[] = data?.data || [];
  const total: number = data?.total || 0;

  function toggle(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  return (
    <div className="animate-in space-y-5">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Activity size={16} className="text-gray-500" />
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Traces</h1>
          <p className="text-sm text-gray-400 mt-0.5">Execution observability</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={executionId}
            onChange={(e) => { setExecutionId(e.target.value); setPage(1); }}
            placeholder="Filter by execution ID"
            className="input pl-8 w-52 text-sm"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="input text-sm w-36"
        >
          <option value="">All statuses</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="running">Running</option>
        </select>
        <button onClick={() => refetch()}
          className="px-3 py-1.5 rounded-lg border border-gray-200 text-xs text-gray-500 hover:bg-gray-50 transition-colors">
          Refresh
        </button>
        {total > 0 && (
          <span className="text-xs text-gray-400 ml-auto">{total} events</span>
        )}
      </div>

      {/* Trace list */}
      {isLoading && <div className="h-32 rounded skeleton" />}

      {!isLoading && traces.length === 0 && (
        <div className="card p-12 text-center text-sm text-gray-400">No traces found.</div>
      )}

      <div className="space-y-1">
        {traces.map((t: any) => {
          const isOpen = expanded.has(String(t.id));
          const dot    = EVENT_DOT[t.event_type] || "bg-gray-300";

          return (
            <div key={t.id} className="card overflow-hidden">
              {/* Row */}
              <button
                onClick={() => toggle(String(t.id))}
                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 transition-colors"
              >
                {isOpen
                  ? <ChevronDown  size={13} className="text-gray-400 shrink-0" />
                  : <ChevronRight size={13} className="text-gray-400 shrink-0" />
                }

                {/* Event dot */}
                <div className={clsx("w-2 h-2 rounded-full shrink-0", dot)} />

                {/* Event type */}
                <span className="font-mono text-xs text-gray-700 w-44 truncate shrink-0">
                  {t.event_type}
                </span>

                {/* Status pill */}
                {t.status && (
                  <span className={clsx(
                    "text-xs px-2 py-0.5 rounded-full capitalize shrink-0",
                    STATUS_PILL[t.status?.toLowerCase()] || "bg-gray-100 text-gray-500"
                  )}>
                    {t.status}
                  </span>
                )}

                {/* Message */}
                <span className="text-xs text-gray-400 flex-1 truncate">
                  {t.message || t.event_source || "—"}
                </span>

                {/* Execution link */}
                {t.workflow_execution_id && (
                  <Link
                    to={`/executions/${t.workflow_execution_id}`}
                    onClick={(e) => e.stopPropagation()}
                    className="text-xs text-gray-400 hover:text-gray-700 inline-flex items-center gap-0.5 shrink-0 transition-colors"
                  >
                    #{t.workflow_execution_id} <ExternalLink size={10} />
                  </Link>
                )}

                {/* Time */}
                <span className="text-xs text-gray-300 font-mono shrink-0 ml-2">
                  {t.created_at ? new Date(t.created_at).toLocaleTimeString() : ""}
                </span>
              </button>

              {/* Expanded detail */}
              {isOpen && (
                <div className="px-4 pb-4 pt-1 border-t border-gray-100 bg-gray-50/40 space-y-3">
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                    {t.trace_id && (
                      <Info label="Trace ID"    value={t.trace_id} mono />
                    )}
                    {t.span_id && (
                      <Info label="Span ID"     value={t.span_id} mono />
                    )}
                    {t.correlation_id && (
                      <Info label="Correlation" value={t.correlation_id} mono />
                    )}
                    {t.workflow_id && (
                      <Info label="Workflow"    value={`#${t.workflow_id}`} />
                    )}
                    {t.workflow_execution_id && (
                      <Info label="Execution"   value={`#${t.workflow_execution_id}`} />
                    )}
                    {t.created_at && (
                      <Info label="Time"        value={new Date(t.created_at).toLocaleString()} />
                    )}
                  </div>

                  {/* Input / Output / Metadata */}
                  {(t.input || t.output || t.metadata) && (
                    <div className="space-y-2">
                      {t.input && (
                        <JsonBlock label="Input" value={t.input} />
                      )}
                      {t.output && (
                        <JsonBlock label="Output" value={t.output} />
                      )}
                      {t.metadata && (
                        <JsonBlock label="Metadata" value={t.metadata} />
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Pagination */}
      {total > 30 && (
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>Page {page} of {Math.ceil(total / 30)}</span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-40 transition-colors"
            >
              Prev
            </button>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={traces.length < 30}
              className="px-3 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-40 transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// ── Shared bits ───────────────────────────────────────────────────────────────
const Info = ({ label, value, mono }: { label: string; value: string; mono?: boolean }) => (
  <div>
    <p className="text-gray-400 mb-0.5">{label}</p>
    <p className={clsx("text-gray-700 truncate", mono && "font-mono")}>{value}</p>
  </div>
);

const JsonBlock = ({ label, value }: { label: string; value: any }) => (
  <div>
    <p className="text-xs text-gray-400 mb-0.5">{label}</p>
    <pre className="text-xs font-mono text-gray-600 bg-white border border-gray-100 rounded-lg p-2.5 overflow-x-auto max-h-36">
      {typeof value === "string" ? value : JSON.stringify(value, null, 2)}
    </pre>
  </div>
);

export default Traces;
