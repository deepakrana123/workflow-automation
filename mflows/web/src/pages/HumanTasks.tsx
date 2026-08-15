import { useState } from "react";
import { useGetHumanTasksQuery, useDecideHumanTaskMutation } from "@/store/api";
import StatusBadge from "@/components/StatusBadge";
import { Check, X, RefreshCw } from "lucide-react";

const FILTERS = ["PENDING", "APPROVED", "REJECTED"];

const HumanTasks = () => {
  const [status, setStatus] = useState<string>("PENDING");
  const { data: tasks, refetch, isFetching } = useGetHumanTasksQuery(
    { status },
    { pollingInterval: 5000 }
  );
  const [decide, { isLoading }] = useDecideHumanTaskMutation();

  const handle = (id: number, decision: "approve" | "reject") =>
    decide({ id, decision });

  return (
    <div className="animate-in space-y-5">
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

      <div className="flex gap-1.5">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setStatus(f)}
            className={
              "px-3 py-1 rounded-lg text-xs font-medium transition-colors " +
              (status === f
                ? "bg-gray-900 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200")
            }
          >
            {f}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {(tasks || []).map((t: any) => (
          <div key={t.id} className="card p-4 flex items-start gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-900 text-sm">
                  Task #{t.id}
                </span>
                <StatusBadge status={t.status} />
                <span className="text-2xs text-gray-400">
                  exec #{t.workflow_execution_id} · step {t.step_id}
                </span>
              </div>
              <p className="text-sm text-gray-600 mt-1">{t.prompt}</p>
              {t.timeout_at && (
                <p className="text-2xs text-gray-400 mt-1">
                  timeout: {new Date(t.timeout_at).toLocaleString()} (on timeout:{" "}
                  {t.on_timeout})
                </p>
              )}
            </div>

            {t.status === "PENDING" && (
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => handle(t.id, "approve")}
                  disabled={isLoading}
                  className="btn-brand btn-sm"
                >
                  <Check size={12} /> Approve
                </button>
                <button
                  onClick={() => handle(t.id, "reject")}
                  disabled={isLoading}
                  className="btn-secondary btn-sm text-danger"
                >
                  <X size={12} /> Reject
                </button>
              </div>
            )}
          </div>
        ))}

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
