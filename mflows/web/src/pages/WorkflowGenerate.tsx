import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useGenerateWorkflowMutation } from "@/store/api";
import { Sparkles, ArrowLeft } from "lucide-react";
import { FormRenderer } from "@/components/shared/FormRenderer";
import { WORKFLOW_GENERATE_FIELDS, WORKFLOW_GENERATE_DEFAULTS } from "@/config/forms";

const WorkflowGenerate = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState<Record<string, unknown>>({ ...WORKFLOW_GENERATE_DEFAULTS });
  const [generate, { data: result, isLoading, error }] = useGenerateWorkflowMutation();
  const errorMsg = (error as any)?.data?.detail || (error ? "Generation failed" : "");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    generate({
      user_request: form.user_request as string,
      name: form.name as string,
      domain: "finance",
    });
  };

  return (
    <div className="animate-in space-y-5 max-w-xl">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Generate Workflow</h1>
        <p className="text-sm text-gray-500 mt-0.5">Natural language to workflow DAG</p>
      </div>

      <div className="card p-5">
        <FormRenderer
          fields={WORKFLOW_GENERATE_FIELDS}
          values={form}
          onChange={setForm}
          onSubmit={handleSubmit}
          submitLabel={isLoading ? "Generating..." : "Generate"}
          columns={1}
        />
      </div>

      {errorMsg && (
        <div className="card border-red-200 bg-red-50 p-3 text-sm text-danger">{errorMsg}</div>
      )}

      {result && (
        <div className="space-y-4 animate-in">
          <div className="card border-emerald-200 bg-emerald-50 p-3 text-sm text-success font-medium">
            <Sparkles size={14} className="inline mr-1" />
            Created — ID: {result.workflow_id}
          </div>

          <div className="card p-4">
            <h3 className="text-2xs font-semibold text-gray-500 uppercase tracking-wide mb-2">DSL</h3>
            <pre className="text-xs font-mono text-gray-700 bg-gray-50 rounded-lg p-3 overflow-x-auto">
              {result.dsl}
            </pre>
          </div>

          <div className="card p-4">
            <h3 className="text-2xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Steps</h3>
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

          {result.explanation && (
            <div className="card p-4">
              <h3 className="text-2xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Why this workflow
              </h3>
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

          <button onClick={() => navigate("/workflows")} className="inline-flex items-center gap-1 text-sm text-brand-600 hover:underline">
            <ArrowLeft size={13} /> Back
          </button>
        </div>
      )}
    </div>
  );
};

export default WorkflowGenerate;
