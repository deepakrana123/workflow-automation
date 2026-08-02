import { useState } from "react";
import { useParams } from "react-router-dom";
import { useGetWorkflowQuery, useExecuteWorkflowMutation } from "@/store/api";
import StatusBadge from "@/components/StatusBadge";
import { Play } from "lucide-react";

export default function WorkflowDetail() {
  const { id } = useParams();
  const { data: workflow } = useGetWorkflowQuery(Number(id));
  const [execute, { data: execResult, isLoading: executing }] = useExecuteWorkflowMutation();
  const [entityId, setEntityId] = useState("");

  if (!workflow) return <p className="text-gray-400">Loading...</p>;

  const steps = workflow.parsed_rule_json?.steps || [];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{workflow.name}</h1>
          <p className="text-sm text-gray-500 mt-1">Domain: {workflow.domain} · ID: {workflow.id}</p>
        </div>
        <StatusBadge status={workflow.status || "active"} />
      </div>

      {/* Execute */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 mb-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Execute Workflow</h3>
        <div className="flex gap-3">
          <input
            value={entityId}
            onChange={(e) => setEntityId(e.target.value)}
            placeholder="Entity ID (e.g. LOAN-2024-001)"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500"
          />
          <button
            onClick={() => execute({ workflow_id: workflow.id, entity_id: entityId })}
            disabled={executing || !entityId}
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700 disabled:opacity-50"
          >
            <Play size={14} /> {executing ? "Queuing..." : "Run"}
          </button>
        </div>
        {execResult && (
          <p className="text-xs mt-2 text-emerald-600">
            {execResult.success ? `Queued — execution #${execResult.workflow_execution_id}` : execResult.message}
          </p>
        )}
      </div>

      {/* Steps */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">DAG Steps ({steps.length})</h3>
        <div className="space-y-2">
          {steps.map((step: any) => (
            <div key={step.id} className="flex items-center gap-3 px-3 py-2 bg-gray-50 rounded-lg text-sm">
              <span className="w-6 h-6 bg-brand-100 text-brand-700 rounded-full flex items-center justify-center text-xs font-bold">{step.id}</span>
              <span className="font-medium text-gray-800">{step.action}</span>
              {step.depends_on?.length > 0 && (
                <span className="text-xs text-gray-400">→ depends on: {step.depends_on.join(", ")}</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* DSL */}
      {workflow.raw_input && (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Original Input</h3>
          <p className="text-sm text-gray-600 italic">&ldquo;{workflow.raw_input}&rdquo;</p>
        </div>
      )}
    </div>
  );
}
