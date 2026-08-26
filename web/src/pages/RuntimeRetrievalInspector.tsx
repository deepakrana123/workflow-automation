/**
 * Screen C: Retrieval Inspector (admin/developer only)
 * Shows query → scoped retrieval → ranked candidates with per-source scores.
 */
import { useState } from "react";
import { Search, AlertCircle, Shield, Cpu } from "lucide-react";

const USER_ID = "user_1";
const WORKSPACE_ID = "1";

interface Candidate {
  rank: number;
  action_id: number;
  action_name: string;
  display_name: string;
  description: string;
  workflow_type: string;
  vector_rank: number | null;
  bm25_rank: number | null;
  postgres_rank: number | null;
  rrf_score: number;
  authorized: boolean;
}

export default function RuntimeRetrievalInspector() {
  const [query, setQuery] = useState("");
  const [workflowId, setWorkflowId] = useState("");
  const [topK, setTopK] = useState(10);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch("/api/runtime/retrieve", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Id": USER_ID,
          "X-Workspace-Id": WORKSPACE_ID,
        },
        body: JSON.stringify({
          query,
          workflow_id: workflowId ? Number(workflowId) : null,
          top_k: topK,
          include_diagnostics: true,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Request failed");
      setResult(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const candidates: Candidate[] = result?.retrieval?.top_candidates || [];
  const actor = result?.actor;
  const authz = result?.authorization;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Retrieval Inspector</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Developer tool — inspect scoped retrieval with per-source ranking scores.
        </p>
      </div>

      {/* Query form */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
        <div>
          <label className="text-xs font-medium text-gray-700">Query</label>
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && run()}
            placeholder="e.g. apply interest to loan account"
            className="mt-1 w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30"
          />
        </div>
        <div className="flex gap-3">
          <div className="flex-1">
            <label className="text-xs font-medium text-gray-700">Workflow ID (optional)</label>
            <input
              value={workflowId}
              onChange={e => setWorkflowId(e.target.value)}
              placeholder="e.g. 1"
              className="mt-1 w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-700">Top K</label>
            <select
              value={topK}
              onChange={e => setTopK(Number(e.target.value))}
              className="mt-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none"
            >
              {[5, 10, 20].map(k => <option key={k} value={k}>{k}</option>)}
            </select>
          </div>
        </div>
        <button
          onClick={run}
          disabled={loading || !query.trim()}
          className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-700 disabled:opacity-50 transition-colors"
        >
          <Search size={14} />
          {loading ? "Searching…" : "Run Retrieval"}
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <AlertCircle size={14} /> {error}
        </div>
      )}

      {result && (
        <>
          {/* Context info */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Retrieved", value: result.retrieval?.candidate_count ?? "—", icon: Cpu },
              { label: "Authorized", value: result.retrieval?.authorized_count ?? "—", icon: Shield },
              { label: "Roles", value: actor?.roles?.join(", ") || "—", icon: Shield },
            ].map(({ label, value, icon: Icon }) => (
              <div key={label} className="bg-white border border-gray-200 rounded-xl p-3">
                <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-1">
                  <Icon size={12} />
                  {label}
                </div>
                <p className="text-base font-semibold text-gray-900">{value}</p>
              </div>
            ))}
          </div>

          {/* Results table */}
          {candidates.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-100">
                <h3 className="text-sm font-semibold text-gray-900">Candidates</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-gray-100 text-gray-500">
                      <th className="px-3 py-2 text-left font-medium">Rank</th>
                      <th className="px-3 py-2 text-left font-medium">Action</th>
                      <th className="px-3 py-2 text-center font-medium">Vector</th>
                      <th className="px-3 py-2 text-center font-medium">BM25</th>
                      <th className="px-3 py-2 text-center font-medium">Postgres</th>
                      <th className="px-3 py-2 text-center font-medium">RRF</th>
                      <th className="px-3 py-2 text-center font-medium">Auth</th>
                    </tr>
                  </thead>
                  <tbody>
                    {candidates.map((c: Candidate) => (
                      <tr key={c.action_id} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="px-3 py-2 font-bold text-gray-700">#{c.rank}</td>
                        <td className="px-3 py-2">
                          <p className="font-medium text-gray-900">{c.display_name}</p>
                          <p className="text-gray-400">{c.action_name}</p>
                          {c.description && (
                            <p className="text-gray-400 truncate max-w-xs">{c.description}</p>
                          )}
                        </td>
                        <td className="px-3 py-2 text-center text-gray-600">
                          {c.vector_rank != null ? `#${c.vector_rank}` : "—"}
                        </td>
                        <td className="px-3 py-2 text-center text-gray-600">
                          {c.bm25_rank != null ? `#${c.bm25_rank}` : "—"}
                        </td>
                        <td className="px-3 py-2 text-center text-gray-600">
                          {c.postgres_rank != null ? `#${c.postgres_rank}` : "—"}
                        </td>
                        <td className="px-3 py-2 text-center font-mono text-blue-700">
                          {c.rrf_score.toFixed(5)}
                        </td>
                        <td className="px-3 py-2 text-center">
                          <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                            c.authorized
                              ? "bg-green-50 text-green-700"
                              : "bg-red-50 text-red-700"
                          }`}>
                            {c.authorized ? "Yes" : "No"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {candidates.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-8">
              No authorized candidates found for this query.
            </p>
          )}
        </>
      )}
    </div>
  );
}
