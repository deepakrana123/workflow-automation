import { useParams } from "react-router-dom";
import { useGetExecutionQuery, usePauseExecutionMutation, useResumeExecutionMutation } from "@/store/api";
import StatusBadge from "@/components/StatusBadge";
import { Pause, Play, RefreshCw } from "lucide-react";
import { clsx } from "clsx";

const ExecutionDetail = () => {
  const { id } = useParams();
  const { data: exec, refetch } = useGetExecutionQuery(id!, { pollingInterval: 5000 });
  const [pause] = usePauseExecutionMutation();
  const [resume] = useResumeExecutionMutation();

  if (!exec) return <div className="h-6 w-40 rounded skeleton mt-8" />;

  return (
    <div className="animate-in space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Execution #{exec.id}</h1>
          <p className="text-sm text-gray-500 mt-0.5">{exec.workflow_name} · {exec.trace_id || "—"}</p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={exec.status} />
          {exec.status === "running" && <button onClick={() => pause(Number(exec.id))} className="btn-secondary btn-sm"><Pause size={12}/> Pause</button>}
          {exec.status === "paused" && <button onClick={() => resume(Number(exec.id))} className="btn-brand btn-sm"><Play size={12}/> Resume</button>}
          <button onClick={() => refetch()} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400"><RefreshCw size={14}/></button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Stat label="Duration" value={exec.duration_ms ? `${(exec.duration_ms/1000).toFixed(2)}s` : "—"} />
        <Stat label="Retries" value={exec.retry_count || 0} />
        <Stat label="Entity" value={exec.entity_id || "—"} />
        <Stat label="Error" value={exec.error || "none"} danger={!!exec.error} />
      </div>

      <div className="card p-5">
        <h2 className="text-sm font-semibold text-gray-900 mb-4">Steps</h2>
        <div className="space-y-0">
          {(exec.steps || []).map((step: any, i: number) => (
            <div key={i} className="flex items-start gap-3 relative pl-5 pb-3.5 last:pb-0">
              {i < (exec.steps?.length || 0) - 1 && <div className="absolute left-[9px] top-4 bottom-0 w-px bg-gray-200" />}
              <div className={clsx("absolute left-[3px] top-1 w-3 h-3 rounded-full border-2 bg-white",
                step.status === "completed" ? "border-success" :
                step.status === "running" ? "border-brand-500 animate-pulse" :
                step.status === "failed" ? "border-danger" : "border-gray-300")} />
              <div className="flex-1 min-w-0 ml-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900 text-sm">{step.name}</span>
                  <StatusBadge status={step.status} />
                  {step.duration_ms && <span className="text-2xs text-gray-400 font-mono">{step.duration_ms}ms</span>}
                </div>
                {step.error && <p className="text-xs text-danger mt-0.5">{step.error}</p>}
              </div>
            </div>
          ))}
          {(!exec.steps || exec.steps.length === 0) && <p className="text-sm text-gray-400">No steps yet.</p>}
        </div>
      </div>
    </div>
  );
}

const Stat = ({ label, value, danger }: { label: string; value: any; danger?: boolean }) => {
  return (
    <div className="card p-4">
      <p className="text-2xs font-medium text-gray-500 mb-1">{label}</p>
      <p className={clsx("text-sm font-semibold truncate", danger ? "text-danger" : "text-gray-900")}>{value}</p>
    </div>
  );
}

export default ExecutionDetail;
