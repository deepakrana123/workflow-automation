import { useGetPromptsQuery, useGetPromptStatsQuery, useActivatePromptMutation, useRollbackPromptMutation } from "@/store/api";
import { RotateCcw, Zap } from "lucide-react";
import { clsx } from "clsx";

const Prompts = () => {
  const { data: prompts = [] } = useGetPromptsQuery();
  const { data: stats = [] } = useGetPromptStatsQuery();
  const [activate] = useActivatePromptMutation();
  const [rollback] = useRollbackPromptMutation();

  return (
    <div className="animate-in space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Prompts</h1>
        <p className="text-sm text-gray-500 mt-0.5">Version management</p>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead><tr className="border-b border-gray-100 bg-gray-50/50">
            <th className="th">Prompt</th><th className="th">Active</th><th className="th">Previous</th><th className="th">Available</th><th className="th">Actions</th>
          </tr></thead>
          <tbody>
            {prompts.map((p: any) => (
              <tr key={p.prompt_name} className="tr">
                <td className="td font-medium text-gray-900 text-sm">{p.prompt_name}</td>
                <td className="td"><span className="badge bg-emerald-50 text-emerald-700">{p.active_version}</span></td>
                <td className="td text-gray-400 text-xs">{p.previous_version || "—"}</td>
                <td className="td text-gray-400 text-xs font-mono">{(p.available_versions || []).join(", ")}</td>
                <td className="td">
                  <div className="flex gap-1">
                    {p.previous_version && <button onClick={() => rollback(p.prompt_name)} className="btn-ghost btn-sm text-warning"><RotateCcw size={11}/> Rollback</button>}
                    {(p.available_versions || []).filter((v: string) => v !== p.active_version).map((v: string) => (
                      <button key={v} onClick={() => activate({ name: p.prompt_name, version: v })} className="btn-ghost btn-sm text-brand-600"><Zap size={11}/> {v}</button>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
            {prompts.length === 0 && <tr><td colSpan={5} className="td text-center py-16 text-gray-400 text-sm">No prompts.</td></tr>}
          </tbody>
        </table>
      </div>

      {stats.length > 0 && <>
        <h2 className="text-sm font-semibold text-gray-900">Performance</h2>
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead><tr className="border-b border-gray-100 bg-gray-50/50">
              <th className="th">Version</th><th className="th">Total</th><th className="th">Pass Rate</th><th className="th">Avg Attempts</th><th className="th">Latency</th>
            </tr></thead>
            <tbody>
              {stats.map((s: any, i: number) => (
                <tr key={i} className="tr">
                  <td className="td font-mono text-xs text-gray-700">{s.prompt_name}/{s.prompt_version}</td>
                  <td className="td text-sm">{s.total}</td>
                  <td className="td"><span className={clsx("font-semibold text-sm", s.pass_rate >= 0.9 ? "text-success" : s.pass_rate >= 0.7 ? "text-warning" : "text-danger")}>{(s.pass_rate*100).toFixed(1)}%</span></td>
                  <td className="td text-sm">{s.avg_attempts}</td>
                  <td className="td text-sm font-mono">{s.avg_latency_ms}ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </>}
    </div>
  );
}

export default Prompts;
