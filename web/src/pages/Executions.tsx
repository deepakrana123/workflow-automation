import { useState } from "react";
import { Link } from "react-router-dom";
import { useGetExecutionsQuery } from "@/store/api";
import StatusBadge from "@/components/StatusBadge";
import { clsx } from "clsx";

const TABS = ["all", "running", "completed", "failed", "dlq"];

const Executions = () => {
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState("all");
  const { data, isLoading } = useGetExecutionsQuery({ page, page_size: 20, status: filter });
  const executions = data?.data || [];
  const total = data?.total || 0;

  return (
    <div className="animate-in space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Executions</h1>
        <p className="text-sm text-gray-500 mt-0.5">{total} total</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-gray-100 rounded-lg w-fit">
        {TABS.map((t) => (
          <button key={t} onClick={() => { setFilter(t); setPage(1); }}
            className={clsx("px-3 py-1.5 text-xs font-medium rounded-md capitalize transition-all",
              filter === t ? "bg-white text-gray-900 shadow-xs" : "text-gray-500 hover:text-gray-700")}>
            {t}
          </button>
        ))}
      </div>

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead><tr className="border-b border-gray-100 bg-gray-50/50">
            <th className="th">ID</th><th className="th">Workflow</th><th className="th">Status</th>
            <th className="th">Duration</th><th className="th">Retries</th><th className="th">Started</th>
          </tr></thead>
          <tbody>
            {executions.map((ex: any) => (
              <tr key={ex.id} className="tr">
                <td className="td"><Link to={`/executions/${ex.id}`} className="font-medium text-brand-600 hover:underline text-sm">#{ex.id}</Link></td>
                <td className="td text-gray-600 text-sm">{ex.workflow_name || "—"}</td>
                <td className="td"><StatusBadge status={ex.status} /></td>
                <td className="td text-gray-500 text-xs font-mono">{ex.duration_ms ? `${(ex.duration_ms/1000).toFixed(1)}s` : "—"}</td>
                <td className="td">{ex.retry_count > 0 ? <span className="badge bg-amber-50 text-amber-700">{ex.retry_count}</span> : <span className="text-gray-400 text-xs">0</span>}</td>
                <td className="td text-gray-500 text-xs">{ex.start_time ? new Date(ex.start_time).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "—"}</td>
              </tr>
            ))}
            {!isLoading && executions.length === 0 && (
              <tr><td colSpan={6} className="td text-center py-16 text-gray-400 text-sm">No executions.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {total > 20 && (
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Page {page} · {total} total</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page===1} className="btn-secondary btn-sm disabled:opacity-40">Prev</button>
            <button onClick={() => setPage(p => p+1)} disabled={executions.length<20} className="btn-secondary btn-sm disabled:opacity-40">Next</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Executions;
