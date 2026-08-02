import { useGetPromptsQuery, useGetPromptStatsQuery, useActivatePromptMutation, useRollbackPromptMutation } from "@/store/api";

export default function Prompts() {
  const { data: prompts = [] } = useGetPromptsQuery();
  const { data: stats = [] } = useGetPromptStatsQuery();
  const [activate] = useActivatePromptMutation();
  const [rollback] = useRollbackPromptMutation();

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Prompt Versions</h1>

      {/* Prompts table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden mb-8">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Prompt</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Active</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Previous</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Versions</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {prompts.map((p: any) => (
              <tr key={p.prompt_name} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{p.prompt_name}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded-full text-xs font-medium">{p.active_version}</span>
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">{p.previous_version || "—"}</td>
                <td className="px-4 py-3 text-gray-500 text-xs">{(p.available_versions || []).join(", ")}</td>
                <td className="px-4 py-3 flex gap-2">
                  {p.previous_version && (
                    <button
                      onClick={() => rollback(p.prompt_name)}
                      className="px-2 py-1 text-xs border border-amber-300 text-amber-700 rounded-md hover:bg-amber-50"
                    >
                      Rollback
                    </button>
                  )}
                  {(p.available_versions || []).filter((v: string) => v !== p.active_version).map((v: string) => (
                    <button
                      key={v}
                      onClick={() => activate({ name: p.prompt_name, version: v })}
                      className="px-2 py-1 text-xs border border-brand-300 text-brand-700 rounded-md hover:bg-brand-50"
                    >
                      Activate {v}
                    </button>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Stats */}
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance Stats</h2>
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Version</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Total</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Pass Rate</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Avg Attempts</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Avg Latency</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {stats.map((s: any, i: number) => (
              <tr key={i} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-xs">{s.prompt_name} / {s.prompt_version}</td>
                <td className="px-4 py-3">{s.total}</td>
                <td className="px-4 py-3">
                  <span className={`font-medium ${s.pass_rate >= 0.9 ? "text-emerald-600" : s.pass_rate >= 0.7 ? "text-amber-600" : "text-red-600"}`}>
                    {(s.pass_rate * 100).toFixed(1)}%
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-600">{s.avg_attempts}</td>
                <td className="px-4 py-3 text-gray-600">{s.avg_latency_ms}ms</td>
              </tr>
            ))}
            {stats.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No stats yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
