import { useState } from "react";
import { useParams } from "react-router-dom";
import {
  useGetWorkflowQuery,
  useExecuteWorkflowMutation,
  useGetWorkflowProvenanceQuery,
} from "@/store/api";
import StatusBadge from "@/components/StatusBadge";
import { Play, GitBranch, FileSearch } from "lucide-react";

const WorkflowDetail = () => {
  const { id } = useParams();
  const { data: workflow } = useGetWorkflowQuery(Number(id));
  const { data: provenance } = useGetWorkflowProvenanceQuery(Number(id));
  const [execute, { data: execResult, isLoading: executing }] = useExecuteWorkflowMutation();
  const [entityId, setEntityId] = useState("");

  if (!workflow) return <div className="h-6 w-40 rounded skeleton mt-8" />;

  const steps = workflow.parsed_rule_json?.steps || [];

  return (
    <div className="animate-in space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">{workflow.name}</h1>
          <p className="text-sm text-gray-500 mt-0.5">Domain: {workflow.domain} · #{workflow.id}</p>
        </div>
        <StatusBadge status={workflow.status || "active"} />
      </div>

      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Execute</h3>
        <div className="flex gap-2">
          <input value={entityId} onChange={e => setEntityId(e.target.value)} placeholder="Entity ID (LOAN-2024-001)" className="input flex-1" />
          <button onClick={() => execute({ workflow_id: workflow.id, entity_id: entityId })} disabled={executing || !entityId} className="btn-brand disabled:opacity-50"><Play size={13}/> {executing ? "..." : "Run"}</button>
        </div>
        {execResult && <p className="text-xs text-success font-medium mt-2">{execResult.success ? `Queued #${execResult.workflow_execution_id}` : execResult.message}</p>}
      </div>

      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-1.5"><GitBranch size={13} className="text-brand-600"/> Steps ({steps.length})</h3>
        <div className="space-y-1.5">
          {steps.map((step: any) => (
            <div key={step.id} className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg text-sm">
              <span className="w-5 h-5 rounded bg-brand-100 text-brand-700 flex items-center justify-center text-2xs font-bold">{step.id}</span>
              <span className="font-medium text-gray-800">{step.action}</span>
              {step.depends_on?.length > 0 && <span className="text-2xs text-gray-400">→ {step.depends_on.join(", ")}</span>}
            </div>
          ))}
        </div>
      </div>

      {workflow.explanation && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-2">Why this workflow</h3>
          <p className="text-sm text-gray-700 mb-3">{workflow.explanation.summary}</p>
          <div className="space-y-2">
            {(workflow.explanation.steps || []).map((s: any) => (
              <div key={s.id} className="flex items-start gap-2 text-sm">
                <span className="w-5 h-5 rounded bg-gray-100 text-gray-600 flex items-center justify-center text-2xs font-bold shrink-0">{s.id}</span>
                <div className="min-w-0">
                  <span className="font-medium text-gray-800">{s.display_name}</span>
                  <p className="text-xs text-gray-500">{s.explanation}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {provenance && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-1.5">
            <FileSearch size={13} className="text-brand-600" /> Provenance
            {provenance.source_document && (
              <span className="text-2xs text-gray-400 font-normal">
                · {provenance.source_document}
              </span>
            )}
            {provenance.average_confidence != null && (
              <span className="text-2xs text-gray-400 font-normal ml-auto">
                avg confidence {(provenance.average_confidence * 100).toFixed(0)}%
              </span>
            )}
          </h3>
          {!provenance.grounded && (
            <p className="text-xs text-gray-400 mb-2">
              Generated from the natural-language request (no BRD source).
            </p>
          )}
          <div className="space-y-2">
            {(provenance.steps || []).map((s: any) => (
              <div key={s.id} className="flex items-start gap-2 text-sm">
                <span className="w-5 h-5 rounded bg-gray-100 text-gray-600 flex items-center justify-center text-2xs font-bold shrink-0">
                  {s.id}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-800">{s.action}</span>
                    {s.source_type === "brd" ? (
                      <span className="text-2xs px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700">
                        BRD{s.source_term ? `: ${s.source_term}` : ""}
                      </span>
                    ) : (
                      <span className="text-2xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">
                        generated
                      </span>
                    )}
                    {s.confidence != null && (
                      <span className="text-2xs text-gray-400 ml-auto">
                        {(s.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  {s.source_clause && (
                    <p className="text-xs text-gray-500 italic mt-0.5">"{s.source_clause}"</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {workflow.raw_input && <div className="card p-5"><h3 className="text-sm font-semibold text-gray-900 mb-2">Input</h3><p className="text-sm text-gray-600 italic">"{workflow.raw_input}"</p></div>}
    </div>
  );
}

export default WorkflowDetail;
