import { useState } from "react";
import { useGetHumanTasksQuery, useDecideHumanTaskMutation } from "@/store/api";
import StatusBadge from "@/components/StatusBadge";
import { Check, X, RefreshCw, ShieldAlert, ChevronsUp } from "lucide-react";
import { clsx } from "clsx";

const FILTERS = ["PENDING", "APPROVED", "REJECTED"];

// ── Role input — shown only for tasks that restrict access ───────────────────
const RoleInput = ({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) => (
  <input
    value={value}
    onChange={(e) => onChange(e.target.value)}
    placeholder="Your role…"
    className="input text-xs w-36 h-7 py-0"
  />
);

// ── Escalation badge ─────────────────────────────────────────────────────────
const EscalationBadge = ({ level }: { level: number }) => {
  if (!level) return null;
  return (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-orange-50 text-orange-600 text-[10px] font-medium">
      <ChevronsUp size={10} />
      L{level}
    </span>
  );
};

const HumanTasks = () => {
  const [status, setStatus]         = useState<string>("PENDING");
  const [roleInputs, setRoleInputs] = useState<Record<number, string>>({});
  const [roleErrors, setRoleErrors] = useState<Record<number, string>>({});

  const { data: tasks, refetch, isFetching } = useGetHumanTasksQuery(
    { status },
    { pollingInterval: 5000 },
  );
  const [decide, { isLoading }] = useDecideHumanTaskMutation();

  const setRole = (id: number, v: string) =>
    setRoleInputs((prev) => ({ ...prev, [id]: v }));

  const handle = async (t: any, decision: "approve" | "reject") => {
    setRoleErrors((prev) => ({ ...prev, [t.id]: "" }));
    try {
      await decide({
        id:         t.id,
        decision,
        actor_role: roleInputs[t.id] || undefined,
      }).unwrap();
    } catch (err: any) {
      // 403 → role not permitted
      const detail = err?.data?.detail || "";
      if (err?.status === 403 || detail.toLowerCase().includes("role")) {
        setRoleErrors((prev) => ({
          ...prev,
          [t.id]: detail || "Your role is not permitted for this task.",
        }));
      }
    }
  };

  return (
    <div className="animate-in space-y-5">

      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Human Tasks</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Approve or reject workflow steps awaiting a decision
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400"
        >
          <RefreshCw size={14} className={isFetching ? "animate-spin" : ""} />
        </button>
      </div>

      {/* ── Filter tabs ── */}
      <div className="flex gap-1.5">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setStatus(f)}
            className={clsx(
              "px-3 py-1 rounded-lg text-xs font-medium transition-colors",
              status === f
                ? "bg-gray-900 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200",
            )}
          >
            {f}
          </button>
        ))}
      </div>

      {/* ── Task cards ── */}
      <div className="space-y-2">
        {(tasks || []).map((t: any) => {
          const hasRoles     = (t.allowed_roles || []).length > 0;
          const roleErrorMsg = roleErrors[t.id] || "";

          return (
            <div key={t.id} className="card p-4 space-y-3">

              {/* Row 1 — identity + status */}
              <div className="flex items-start gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-gray-900 text-sm">
                      Task #{t.id}
                    </span>
                    <StatusBadge status={t.status} />
                    <EscalationBadge level={t.escalation_level} />
                    <span className="text-[11px] text-gray-400">
                      exec #{t.workflow_execution_id} · step {t.step_id}
                    </span>
                  </div>

                  {/* Prompt */}
                  <p className="text-sm text-gray-600 mt-1">{t.prompt}</p>

                  {/* Timeout line */}
                  {t.timeout_at && (
                    <p className="text-[11px] text-gray-400 mt-1">
                      Timeout: {new Date(t.timeout_at).toLocaleString()}
                      {t.on_timeout && (
                        <span className="ml-1 text-gray-300">
                          · auto-{t.on_timeout} on expiry
                        </span>
                      )}
                    </p>
                  )}
                </div>
              </div>

              {/* Row 2 — role info + escalation policy */}
              {(hasRoles || t.escalation_level > 0) && (
                <div className="flex flex-wrap items-center gap-2 text-[11px]">
                  {hasRoles && (
                    <div className="flex items-center gap-1.5 text-gray-500">
                      <ShieldAlert size={11} className="text-gray-400 shrink-0" />
                      <span>Allowed roles:</span>
                      {(t.allowed_roles as string[]).map((r) => (
                        <span
                          key={r}
                          className="px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 font-medium"
                        >
                          {r}
                        </span>
                      ))}
                    </div>
                  )}
                  {t.escalation_level > 0 && t.escalation_policy && (
                    <span className="text-orange-500">
                      Escalation level {t.escalation_level}
                      {t.escalation_policy.max_escalation_levels
                        ? ` / ${t.escalation_policy.max_escalation_levels}`
                        : ""}
                    </span>
                  )}
                </div>
              )}

              {/* Row 3 — action area (PENDING only) */}
              {t.status === "PENDING" && (
                <div className="flex items-center gap-2 flex-wrap">
                  {/* Role input — only shown when task restricts access */}
                  {hasRoles && (
                    <RoleInput
                      value={roleInputs[t.id] || ""}
                      onChange={(v) => setRole(t.id, v)}
                    />
                  )}

                  <button
                    onClick={() => handle(t, "approve")}
                    disabled={isLoading}
                    className="btn-brand btn-sm"
                  >
                    <Check size={12} /> Approve
                  </button>
                  <button
                    onClick={() => handle(t, "reject")}
                    disabled={isLoading}
                    className="btn-secondary btn-sm text-red-600"
                  >
                    <X size={12} /> Reject
                  </button>

                  {/* Role error */}
                  {roleErrorMsg && (
                    <span className="text-[11px] text-red-500 flex-1">
                      {roleErrorMsg}
                    </span>
                  )}
                </div>
              )}

              {/* Resolved info */}
              {t.status !== "PENDING" && t.resolved_at && (
                <p className="text-[11px] text-gray-400">
                  {t.decision} by {t.resolved_by} · {new Date(t.resolved_at).toLocaleString()}
                </p>
              )}

            </div>
          );
        })}

        {(!tasks || tasks.length === 0) && (
          <div className="card p-8 text-center text-sm text-gray-400">
            No {status.toLowerCase()} tasks.
          </div>
        )}
      </div>
    </div>
  );
};

export default HumanTasks;
