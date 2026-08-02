import { useState } from "react";
import { Link } from "react-router-dom";
import { useGetExecutionsQuery } from "@/store/api";
import StatusBadge from "@/components/StatusBadge";

const TABS = ["all", "running", "completed", "failed", "dlq"];

export default function Executions() {
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState("all");

  const { data, isLoading } = useGetExecutionsQuery({ page, page_size: 20, status: filter });
  const executions = data?.data || [];
  const total = data?.total || 0;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Executions</h1>

      <div className="flex gap-1 mb-4 bg-gray-100 p-1 rounded-lg w-fit">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => { setFilter(t); setPage(1); }}
            className={`px-3 py-1.5 text-xs font-medium rounded-md capitalize transition-colors ${
              filter === t ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Workflow</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Duration</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Retries</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Started</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {executions.map((ex: any) => (
              <tr key={ex.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3">
                  <Link to={`/executions/${ex.id}`} className="text-brand-600 hover:underline font-medium">#{ex.id}</Link>
                </td>
                <td className="px-4 py-3 text-gray-700">{ex.workflow_name || "—"}</td>
                <td className="px-4 py-3"><StatusBadge status={ex.status} /></td>
                <td className="px-4 py-3 text-gray-500">{ex.duration_ms ? `${(ex.duration_ms / 1000).toFixed(1)}s` : "—"}</td>
                <td className="px-4 py-3 text-gray-500">{ex.retry_count || 0}</td>
                <td className="px-4 py-3 text-gray-500">{ex.start_time ? new Date(ex.start_time).toLocaleString() : "—"}</td>
              </tr>
            ))}
            {!isLoading && executions.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-12 text-center text-gray-400">No executions found.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {total > 20 && (
        <div className="flex items-center justify-between mt-4 text-sm text-gray-500">
          <span>Page {page} · {total} total</span>
          <div className="flex gap-2">
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-40">Prev</button>
            <button onClick={() => setPage((p) => p + 1)} disabled={executions.length < 20} className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-40">Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
