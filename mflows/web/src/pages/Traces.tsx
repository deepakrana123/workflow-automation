import { useState } from "react";
import { useGetTracesQuery } from "@/store/api";
import StatusBadge from "@/components/StatusBadge";

export default function Traces() {
  const [page, setPage] = useState(1);
  const [executionId, setExecutionId] = useState("");
  const { data } = useGetTracesQuery({ page, page_size: 30, execution_id: executionId || undefined });
  const traces = data?.data || [];
  const total = data?.total || 0;
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Traces</h1>

      <div className="mb-4">
        <input
          type="text"
          value={executionId}
          onChange={(e) => { setExecutionId(e.target.value); setPage(1); }}
          placeholder="Filter by execution ID..."
          className="px-4 py-2 border border-gray-300 rounded-lg text-sm w-64 focus:ring-2 focus:ring-brand-500 outline-none"
        />
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Event</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Source</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Message</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {traces.map((t: any) => (
              <>
                <tr
                  key={t.id}
                  onClick={() => setExpanded(expanded === t.id ? null : t.id)}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3 font-mono text-xs text-gray-800">{t.event_type}</td>
                  <td className="px-4 py-3 text-gray-600 text-xs">{t.event_source || "—"}</td>
                  <td className="px-4 py-3"><StatusBadge status={t.status || "unknown"} /></td>
                  <td className="px-4 py-3 text-gray-500 text-xs truncate max-w-xs">{t.message || "—"}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{t.created_at ? new Date(t.created_at).toLocaleTimeString() : "—"}</td>
                </tr>
                {expanded === t.id && (
                  <tr key={`${t.id}-detail`}>
                    <td colSpan={5} className="px-4 py-3 bg-gray-50">
                      <pre className="text-xs bg-gray-900 text-green-400 p-3 rounded-lg overflow-x-auto max-h-48">
                        {JSON.stringify({ input: t.input, output: t.output, metadata: t.metadata }, null, 2)}
                      </pre>
                    </td>
                  </tr>
                )}
              </>
            ))}
            {traces.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-12 text-center text-gray-400">No trace events found.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {total > 30 && (
        <div className="flex items-center justify-between mt-4 text-sm text-gray-500">
          <span>Page {page} · {total} total</span>
          <div className="flex gap-2">
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-40">Prev</button>
            <button onClick={() => setPage((p) => p + 1)} disabled={traces.length < 30} className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-40">Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
