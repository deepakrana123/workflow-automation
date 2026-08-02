import { useState } from "react";
import { useGetTriggersQuery, useGetActionsQuery } from "@/store/api";

export default function Catalog() {
  const [tab, setTab] = useState<"triggers" | "actions">("actions");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const triggerQuery = useGetTriggersQuery({ page, page_size: 30, search }, { skip: tab !== "triggers" });
  const actionQuery = useGetActionsQuery({ page, page_size: 30, search }, { skip: tab !== "actions" });

  const data = tab === "triggers" ? triggerQuery.data : actionQuery.data;
  const items = data?.data || [];
  const total = data?.total || 0;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Banking Catalog</h1>

      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
          <button onClick={() => { setTab("triggers"); setPage(1); }} className={`px-4 py-1.5 text-xs font-medium rounded-md ${tab === "triggers" ? "bg-white shadow-sm text-gray-900" : "text-gray-500"}`}>
            Triggers
          </button>
          <button onClick={() => { setTab("actions"); setPage(1); }} className={`px-4 py-1.5 text-xs font-medium rounded-md ${tab === "actions" ? "bg-white shadow-sm text-gray-900" : "text-gray-500"}`}>
            Actions ({total})
          </button>
        </div>
        <input
          type="text"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          placeholder="Search catalog..."
          className="px-4 py-2 border border-gray-300 rounded-lg text-sm w-64 focus:ring-2 focus:ring-brand-500 outline-none"
        />
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Display Name</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Description</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {items.map((item: any) => (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-xs text-gray-800">{item.name}</td>
                <td className="px-4 py-3 font-medium text-gray-900">{item.display_name}</td>
                <td className="px-4 py-3 text-gray-500 text-xs truncate max-w-md">{item.description || "—"}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td colSpan={3} className="px-4 py-12 text-center text-gray-400">No items found.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {total > 30 && (
        <div className="flex items-center justify-between mt-4 text-sm text-gray-500">
          <span>Page {page} · {total} total</span>
          <div className="flex gap-2">
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-40">Prev</button>
            <button onClick={() => setPage((p) => p + 1)} disabled={items.length < 30} className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-40">Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
