/**
 * Screen E: RBAC Inspector
 * Shows the current user's roles, permissions, accessible workflows, and allowed capabilities.
 */
import { useState, useEffect } from "react";
import { User, Shield, GitBranch, Cpu, AlertCircle, CheckCircle } from "lucide-react";

const USER_ID = "user_1";
const WORKSPACE_ID = "1";

const PERMISSION_GROUPS: Record<string, string[]> = {
  Workflow:    ["workflow:read", "workflow:create", "workflow:publish", "workflow:delete"],
  Rules:       ["rule:read", "rule:create", "rule:override"],
  HumanTasks:  ["humantask:read", "humantask:resolve", "humantask:escalate"],
  Admin:       ["admin:manage_roles", "audit:read", "capability:read"],
};

export default function RuntimeRBACInspector() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/runtime/rbac/me", {
      headers: { "X-User-Id": USER_ID, "X-Workspace-Id": WORKSPACE_ID },
    })
      .then(r => r.json())
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Loading…</div>;

  const permissions: string[] = data?.permissions || [];
  const roles: string[]        = data?.roles || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">RBAC Inspector</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Effective permissions for user <code className="bg-gray-100 px-1 rounded">{USER_ID}</code>{" "}
          in workspace <code className="bg-gray-100 px-1 rounded">{WORKSPACE_ID}</code>
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <AlertCircle size={14} /> {error}
        </div>
      )}

      {data && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              { label: "Roles", value: roles.length, icon: User, color: "text-blue-700" },
              { label: "Permissions", value: permissions.length, icon: Shield, color: "text-green-700" },
              { label: "Accessible Workflows", value: data.accessible_workflows ?? "—", icon: GitBranch, color: "text-purple-700" },
              { label: "Allowed Actions", value: data.allowed_action_count ?? "—", icon: Cpu, color: "text-amber-700" },
            ].map(({ label, value, icon: Icon, color }) => (
              <div key={label} className="bg-white border border-gray-200 rounded-xl p-4">
                <div className="flex items-center gap-2 text-gray-500 text-xs mb-2">
                  <Icon size={13} />
                  {label}
                </div>
                <p className={`text-2xl font-bold ${color}`}>{value}</p>
              </div>
            ))}
          </div>

          {/* Roles */}
          <div className="bg-white border border-gray-200 rounded-xl p-4">
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Assigned Roles</h2>
            {roles.length === 0 ? (
              <p className="text-sm text-gray-400">No roles assigned. Contact your administrator.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {roles.map(r => (
                  <span key={r} className="px-3 py-1 bg-blue-50 text-blue-800 border border-blue-200 rounded-full text-xs font-medium">
                    {r}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Permission matrix */}
          <div className="bg-white border border-gray-200 rounded-xl p-4">
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Permission Matrix</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(PERMISSION_GROUPS).map(([group, perms]) => (
                <div key={group}>
                  <p className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">{group}</p>
                  <div className="space-y-1">
                    {perms.map(p => {
                      const granted = permissions.includes(p);
                      return (
                        <div key={p} className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs ${
                          granted ? "bg-green-50" : "bg-gray-50"
                        }`}>
                          {granted
                            ? <CheckCircle size={12} className="text-green-500 shrink-0" />
                            : <div className="w-3 h-3 rounded-full border border-gray-300 shrink-0" />
                          }
                          <span className={granted ? "text-gray-900 font-medium" : "text-gray-400"}>
                            {p}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Blocked capabilities */}
          {permissions.length === 0 && (
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl">
              <p className="text-sm text-amber-800 font-medium">No permissions resolved.</p>
              <p className="text-xs text-amber-600 mt-1">
                This means no RoleAssignment exists for user <strong>{USER_ID}</strong> in workspace {WORKSPACE_ID} or any ancestor.
                Run RBAC extraction and assign a role via <code>/api/rbac/assign</code>.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
