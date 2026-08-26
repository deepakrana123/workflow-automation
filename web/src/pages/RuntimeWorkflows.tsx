/**
 * Screen A: Runtime Workflow List
 * Shows accessible workflows for the current user/workspace with role and status context.
 */
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { GitBranch, Shield, Activity, ChevronRight, AlertCircle } from "lucide-react";

const USER_ID = "user_1";
const WORKSPACE_ID = "1";

interface WorkflowItem {
  id: number;
  name: string;
  status: string;
  domain: string;
  workspace_id: number;
  step_count: number;
}

const StatusBadge = ({ status }: { status: string }) => {
  const color =
    status === "published" ? "bg-green-50 text-green-700 border-green-200" :
    status === "active"    ? "bg-blue-50 text-blue-700 border-blue-200" :
                             "bg-gray-50 text-gray-600 border-gray-200";
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${color}`}>
      {status.toUpperCase()}
    </span>
  );
};

export default function RuntimeWorkflows() {
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const headers = { "X-User-Id": USER_ID, "X-Workspace-Id": WORKSPACE_ID };

    Promise.all([
      fetch("/api/runtime/workflows", { headers }).then(r => r.json()),
      fetch("/api/runtime/rbac/me", { headers }).then(r => r.json()),
    ])
      .then(([wfData, rbacData]) => {
        setWorkflows(wfData.workflows || []);
        setRoles(rbacData.roles || []);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Loading…</div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Runtime Workflows</h1>
          <p className="text-sm text-gray-500 mt-0.5">Workflows accessible to your role and workspace</p>
        </div>
        <div className="flex items-center gap-2">
          <Shield size={14} className="text-blue-500" />
          <span className="text-xs text-gray-600 font-medium">
            Roles: {roles.length ? roles.join(", ") : "none assigned"}
          </span>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <AlertCircle size={14} />
          {error}
        </div>
      )}

      {!error && workflows.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <GitBranch size={32} className="mx-auto mb-3 opacity-40" />
          <p className="text-sm">No accessible workflows found for your role.</p>
          <p className="text-xs mt-1">Contact your administrator to assign a role.</p>
        </div>
      )}

      <div className="grid gap-3">
        {workflows.map(wf => (
          <Link
            key={wf.id}
            to={`/runtime/workflows/${wf.id}`}
            className="block bg-white border border-gray-200 rounded-xl p-4 hover:border-gray-300 hover:shadow-sm transition-all"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-lg bg-gray-900 flex items-center justify-center shrink-0">
                  <GitBranch size={16} className="text-white" />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 text-sm">{wf.name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-gray-500">{wf.domain}</span>
                    <span className="text-gray-300">·</span>
                    <span className="text-xs text-gray-500">{wf.step_count} steps</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <StatusBadge status={wf.status} />
                <div className="flex items-center gap-1 text-xs text-gray-400">
                  <Activity size={12} />
                  <span>Role: {roles[0] || "—"}</span>
                </div>
                <ChevronRight size={14} className="text-gray-400" />
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
