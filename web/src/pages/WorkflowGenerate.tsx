// ── DEPRECATED ────────────────────────────────────────────────────────────────
// This page (global catalog generation) is disabled.
// Workflow generation is now workspace-scoped:
//   Workspaces → select a workspace → "Build with AI" → /workspaces/:id/build
//
// The global generation path (no workspace context) produces workflows that may
// include actions irrelevant to the user's actual BRDs. All generation should
// start from a workspace so the LLM is grounded in that workspace's knowledge.
//
// To re-enable global generation, uncomment this component and restore the
// route in App.tsx.
// ─────────────────────────────────────────────────────────────────────────────

// import { useState } from "react";
// import { useNavigate } from "react-router-dom";
// import { useGenerateWorkflowMutation } from "@/store/api";
// import { Sparkles, ArrowLeft } from "lucide-react";
// import { FormRenderer } from "@/components/shared/FormRenderer";
// import { WORKFLOW_GENERATE_FIELDS, WORKFLOW_GENERATE_DEFAULTS } from "@/config/forms";

// const WorkflowGenerate = () => { ... };

import { Link } from "react-router-dom";
import { FolderKanban, Sparkles } from "lucide-react";
import { useGetWorkspacesQuery } from "@/store/api";

const WorkflowGenerate = () => {
  const { data: workspaces } = useGetWorkspacesQuery();

  return (
    <div className="animate-in space-y-5 max-w-xl">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Build a Workflow</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Select a workspace — workflows are generated from its BRD knowledge, not the global catalog.
        </p>
      </div>

      <div className="space-y-2">
        {(workspaces || []).map((w: any) => (
          <Link
            key={w.id}
            to={`/workspaces/${w.id}/build`}
            className="card p-4 flex items-center gap-3 hover:border-brand-300 transition-colors group"
          >
            <div className="w-9 h-9 rounded-lg bg-brand-50 flex items-center justify-center group-hover:bg-brand-100 transition-colors">
              <FolderKanban size={16} className="text-brand-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">{w.display_name}</p>
              <p className="text-2xs text-gray-400">{w.name}{w.organization_name ? ` · ${w.organization_name}` : ""}</p>
            </div>
            <span className="inline-flex items-center gap-1 text-xs text-brand-600 font-medium">
              <Sparkles size={12} /> Build with AI
            </span>
          </Link>
        ))}
        {(!workspaces || workspaces.length === 0) && (
          <div className="card p-8 text-center text-sm text-gray-400">
            No workspaces yet.{" "}
            <Link to="/workspaces" className="text-brand-600 underline">Create one</Link> then upload BRDs.
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowGenerate;
