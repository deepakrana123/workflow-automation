/**
 * Screen B: Workflow Execution View
 * Visualizes execution step DAG with status, role requirements, rule evaluation, and output.
 */
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { CheckCircle, Circle, XCircle, Clock, Lock, ChevronDown, ChevronUp, AlertCircle } from "lucide-react";

const USER_ID = "user_1";
const WORKSPACE_ID = "1";

const STATUS_CONFIG: Record<string, { icon: typeof CheckCircle; color: string; label: string }> = {
  completed: { icon: CheckCircle, color: "text-green-500", label: "Completed" },
  running:   { icon: Circle, color: "text-blue-500", label: "Running" },
  waiting:   { icon: Clock, color: "text-amber-500", label: "Waiting" },
  blocked:   { icon: Lock, color: "text-red-400", label: "Blocked" },
  failed:    { icon: XCircle, color: "text-red-500", label: "Failed" },
  pending:   { icon: Circle, color: "text-gray-300", label: "Pending" },
  skipped:   { icon: Circle, color: "text-gray-300", label: "Skipped" },
};

interface Step {
  id: string;
  step_id: string;
  step_name: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  attempts: number;
  last_error: string | null;
  rule_evaluation: any;
}

function StepCard({ step, index }: { step: Step; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const cfg = STATUS_CONFIG[step.status] || STATUS_CONFIG.pending;
  const Icon = cfg.icon;

  return (
    <div className={`border rounded-xl overflow-hidden ${
      step.status === "running" ? "border-blue-200 bg-blue-50/30" :
      step.status === "blocked" ? "border-red-200 bg-red-50/30" :
      step.status === "failed"  ? "border-red-200" :
      step.status === "completed" ? "border-green-100" :
      "border-gray-200 bg-white"
    }`}>
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center gap-3 p-3 text-left"
      >
        <span className="text-xs text-gray-400 w-5 text-center">{index + 1}</span>
        <Icon size={16} className={cfg.color} />
        <span className="flex-1 text-sm font-medium text-gray-900">{step.step_name}</span>
        <span className={`text-xs font-medium ${cfg.color}`}>{cfg.label}</span>
        {step.rule_evaluation && (
          <span className={`text-xs px-1.5 py-0.5 rounded ${
            step.rule_evaluation.passed ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
          }`}>
            Rules: {step.rule_evaluation.passed ? "✓" : "✗"}
          </span>
        )}
        {expanded ? <ChevronUp size={14} className="text-gray-400" /> : <ChevronDown size={14} className="text-gray-400" />}
      </button>

      {expanded && (
        <div className="px-3 pb-3 pt-1 border-t border-gray-100 space-y-2">
          <div className="flex gap-4 text-xs text-gray-500">
            {step.started_at && <span>Started: {new Date(step.started_at).toLocaleTimeString()}</span>}
            {step.completed_at && <span>Done: {new Date(step.completed_at).toLocaleTimeString()}</span>}
            {step.attempts > 0 && <span>Attempts: {step.attempts}</span>}
          </div>

          {step.last_error && (
            <div className="text-xs text-red-600 bg-red-50 p-2 rounded">
              Error: {step.last_error}
            </div>
          )}

          {step.rule_evaluation && (
            <div className="bg-white border border-gray-100 rounded-lg p-2">
              <p className="text-xs font-medium text-gray-700 mb-1">Rule Evaluation</p>
              <div className="text-xs text-gray-600">
                Passed: {step.rule_evaluation.passed_count}/{step.rule_evaluation.total}
                {step.rule_evaluation.blocking_rule && (
                  <div className="mt-1 text-red-600">
                    Blocked by: {step.rule_evaluation.blocking_rule.description}
                  </div>
                )}
              </div>
            </div>
          )}

          {(step.status === "waiting" || step.status === "blocked") && (
            <div className="text-xs text-amber-700 bg-amber-50 p-2 rounded">
              {step.status === "waiting"
                ? "Waiting for human approval"
                : "Blocked by business rule — not retried"}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function RuntimeExecutionView() {
  const { id } = useParams<{ id: string }>();
  const [state, setState] = useState<any>(null);
  const [steps, setSteps] = useState<Step[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const headers = { "X-User-Id": USER_ID, "X-Workspace-Id": WORKSPACE_ID };
    Promise.all([
      fetch(`/api/runtime/executions/${id}`, { headers }).then(r => r.json()),
      fetch(`/api/runtime/executions/${id}/steps`, { headers }).then(r => r.json()),
    ])
      .then(([stateData, stepsData]) => {
        setState(stateData);
        setSteps(stepsData.steps || []);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Loading…</div>;
  if (error) return (
    <div className="flex items-center gap-2 p-4 bg-red-50 rounded-xl text-red-700 text-sm">
      <AlertCircle size={14} /> {error}
    </div>
  );
  if (!state) return <div className="text-sm text-gray-500">Execution not found.</div>;

  const exec = state.execution;
  const wf = state.workflow;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-gray-900">
          {wf?.name || `Execution #${id}`}
        </h1>
        <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
          <span>Execution #{id}</span>
          <span className="text-gray-300">·</span>
          <span className={`font-medium ${
            exec?.status === "completed" ? "text-green-600" :
            exec?.status === "failed" ? "text-red-600" :
            exec?.status === "running" ? "text-blue-600" : "text-gray-600"
          }`}>{(exec?.status || "unknown").toUpperCase()}</span>
          {exec?.started_at && (
            <>
              <span className="text-gray-300">·</span>
              <span>Started {new Date(exec.started_at).toLocaleString()}</span>
            </>
          )}
        </div>
      </div>

      {/* Current step indicator */}
      {exec?.current_step_name && (
        <div className="flex items-center gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
          <Circle size={14} className="animate-pulse" />
          Currently at step: <strong>{exec.current_step_name}</strong>
        </div>
      )}

      {/* Step timeline */}
      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-3">
          Steps ({steps.length})
        </h2>
        <div className="space-y-2">
          {steps.map((step, i) => (
            <StepCard key={step.id} step={step} index={i} />
          ))}
        </div>
        {steps.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-8">No steps recorded yet.</p>
        )}
      </div>
    </div>
  );
}
