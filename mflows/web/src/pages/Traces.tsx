import { useState } from "react";
import { useGetTracesQuery } from "@/store/api";
import StatusBadge from "@/components/StatusBadge";
import { Search, ChevronRight, ChevronDown } from "lucide-react";

const Traces = () => {
  const [page, setPage] = useState(1);
  const [executionId, setExecutionId] = useState("");
  const { data } = useGetTracesQuery({ page, page_size: 30, execution_id: executionId || undefined });
  const traces = data?.data || [];
  const total = data?.total || 0;
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="animate-in space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Traces</h1>
          <p className="text-sm text-gray-500 mt-0.5">Distributed tracing</p>
        </div>
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input value={executionId} onChange={(e) => { setExecutionId(e.target.value); setPage(1); }} placeholder="Filter by execution ID" className="input pl-9 w-56" />
        </div>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead><tr className="border-b border-gray-100 bg-gray-50/50">
            <th className="th w-8"></th><th className="th">Event</th><th className="th">Source</th><th className="th">Status</th><th className="th">Message</th><th className="th">Time</th>
          </tr></thead>
          <tbody>
            {traces.map((t: any) => (
              <tbody key={t.id}>
                <tr onClick={() => setExpanded(expanded === t.id ? null : t.id)} className="tr cursor-pointer">
                  <td className="td w-8 text-gray-400">{expanded === t.id ? <ChevronDown size={13}/> : <ChevronRight size={13}/>}</td>
                  <td className="td font-mono text-xs text-gray-800">{t.event_type}</td>
                  <td className="td text-gray-500 text-xs">{t.event_source || "—"}</td>
                  <td className="td"><StatusBadge status={t.status || "unknown"} /></td>
                  <td className="td text-gray-400 text-xs truncate max-w-[180px]">{t.message || "—"}</td>
                  <td className="td text-gray-400 text-xs font-mono">{t.created_at ? new Date(t.created_at).toLocaleTimeString() : "—"}</td>
                </tr>
                {expanded === t.id && (
                  <tr><td colSpan={6} className="px-4 py-3 bg-gray-50">
                    <pre className="text-xs font-mono text-gray-700 bg-white border border-gray-200 rounded-lg p-3 overflow-x-auto max-h-48 scroll-thin">{JSON.stringify({ input: t.input, output: t.output, metadata: t.metadata }, null, 2)}</pre>
                  </td></tr>
                )}
              </tbody>
            ))}
            {traces.length === 0 && <tr><td colSpan={6} className="td text-center py-16 text-gray-400 text-sm">No traces.</td></tr>}
          </tbody>
        </table>
      </div>

      {total > 30 && (
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Page {page} · {total} total</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1,p-1))} disabled={page===1} className="btn-secondary btn-sm disabled:opacity-40">Prev</button>
            <button onClick={() => setPage(p => p+1)} disabled={traces.length<30} className="btn-secondary btn-sm disabled:opacity-40">Next</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Traces;
