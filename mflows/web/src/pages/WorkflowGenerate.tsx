import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useGenerateWorkflowMutation } from "@/store/api";
import { Sparkles } from "lucide-react";

export default function WorkflowGenerate() {
  const navigate = useNavigate();
  const [request, setRequest] = useState("");
  const [name, setName] = useState("");
  const [generate, { data: result, isLoading, error }] = useGenerateWorkflowMutation();

  const errorMsg = (error as any)?.data?.detail || (error ? "Generation failed" : "");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    generate({ user_request: request, name, domain: "finance" });
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Generate Workflow</h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Workflow Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. loan_collection_flow"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Banking Workflow Instruction</label>
          <textarea
            value={request}
            onChange={(e) => setRequest(e.target.value)}
            placeholder="e.g. when payment is missed send reminder then assign recovery agent and escalate to collections"
            rows={4}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none resize-none"
            required
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Sparkles size={16} />
          {isLoading ? "Generating..." : "Generate Workflow"}
        </button>
      </form>

      {errorMsg && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {errorMsg}
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-sm text-emerald-800">
            Workflow created — ID: {result.workflow_id}
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">DSL</h3>
            <pre className="text-xs bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto">
              {result.dsl}
            </pre>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Steps</h3>
            <div className="space-y-2">
              {result.parsed_rule_json?.steps?.map((step: any) => (
                <div key={step.id} className="flex items-center gap-3 px-3 py-2 bg-gray-50 rounded-lg text-sm">
                  <span className="w-6 h-6 bg-brand-100 text-brand-700 rounded-full flex items-center justify-center text-xs font-bold">
                    {step.id}
                  </span>
                  <span className="font-medium text-gray-800">{step.action}</span>
                  {step.depends_on?.length > 0 && (
                    <span className="text-xs text-gray-400">depends on: {step.depends_on.join(", ")}</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          <button onClick={() => navigate("/workflows")} className="text-sm text-brand-600 hover:underline">
            ← Back to Workflows
          </button>
        </div>
      )}
    </div>
  );
}
