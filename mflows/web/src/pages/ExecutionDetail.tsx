import { useParams } from "react-router-dom";
import { useGetExecutionQuery, usePauseExecutionMutation, useResumeExecutionMutation } from "@/store/api";
import StatusBadge from "@/components/StatusBadge";
import { Pause, Play, RefreshCw } from "lucide-react";

export default function ExecutionDetail() {
  const { id } = useParams();
  const { data: exec, refetch } = useGetExecutionQuery(id!, { pollingInterval: 5000 });
  const [pause] = usePauseExecutionMutation();
  const [resume] = useResumeExecutionMutation();

  if (!exec) return <p className="text-gray-400">Loading...</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Execution #{exec.id}</h1>
          <p className="text-sm text-gray-500 mt-1">{exec.workflow_name} · trace: {exec.trace_id || "—"}</p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={exec.status} />
          {exec.status === "running" && (
            <button onClick={() => pause(Number(exec.id))} className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium border border-gray-300 rounded-lg hover:bg-gray-50">
              <Pause size={14} /> Pause
            </button>
          )}
          {exec.status === "paused" && (
            <button onClick={() => resume(Number(exec.id))} className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium border border-gray-300 rounded-lg hover:bg-gray-50">
              <Play size={14} /> Resume
            </button>
          )}
          <button onClick={() => refetch()} className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-xs text-gray-500">Duration</p>
          <p className="text-lg font-semibold">{exec.duration_ms ? `${(exec.duration_ms / 1000).toFixed(2)}s` : "—"}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-xs text-gray-500">Retries</p>
          <p className="text-lg font-semibold">{exec.retry_count || 0}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-xs text-gray-500">Entity</p>
          <p className="text-lg font-semibold truncate">{exec.entity_id || "—"}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-xs text-gray-500">Error</p>
          <p className="text-sm text-red-600 truncate">{exec.error || "none"}</p>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Steps</h2>
        <div className="space-y-3">
          {(exec.steps || []).map((step: any, i: number) => (
            <div key={i} className="flex items-start gap-4 pl-4 border-l-2 border-gray-200 pb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900 text-sm">{step.name}</span>
                  <StatusBadge status={step.status} />
                  {step.duration_ms && <span className="text-xs text-gray-400">{step.duration_ms}ms</span>}
                </div>
                {step.error && <p className="text-xs text-red-500 mt-1">{step.error}</p>}
              </div>
            </div>
          ))}
          {(!exec.steps || exec.steps.length === 0) && (
            <p className="text-sm text-gray-400">No steps recorded yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
