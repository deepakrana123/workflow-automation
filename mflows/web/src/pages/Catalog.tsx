import { useState } from "react";
import { useGetTriggersQuery, useGetActionsQuery } from "@/store/api";
import { Search } from "lucide-react";
import { clsx } from "clsx";

const Catalog = () => {
  const [tab, setTab] = useState<"triggers" | "actions">("actions");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const triggerQuery = useGetTriggersQuery({ page, page_size: 30, search }, { skip: tab !== "triggers" });
  const actionQuery = useGetActionsQuery({ page, page_size: 30, search }, { skip: tab !== "actions" });
  const data = tab === "triggers" ? triggerQuery.data : actionQuery.data;
  const items = data?.data || [];
  const total = data?.total || 0;

  return (
    <div className="animate-in space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Catalog</h1>
          <p className="text-sm text-gray-500 mt-0.5">Triggers & actions</p>
        </div>
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder="Search..." className="input pl-9 w-56" />
        </div>
      </div>

      <div className="flex gap-1 p-1 bg-gray-100 rounded-lg w-fit">
        {(["triggers", "actions"] as const).map(t => (
          <button key={t} onClick={() => { setTab(t); setPage(1); }}
            className={clsx("px-3 py-1.5 text-xs font-medium rounded-md capitalize transition-all",
              tab === t ? "bg-white text-gray-900 shadow-xs" : "text-gray-500 hover:text-gray-700")}>
            {t} {tab === t && `(${total})`}
          </button>
        ))}
      </div>

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead><tr className="border-b border-gray-100 bg-gray-50/50">
            <th className="th">Name</th><th className="th">Display Name</th><th className="th">Description</th>
          </tr></thead>
          <tbody>
            {items.map((item: any) => (
              <tr key={item.id} className="tr">
                <td className="td"><code className="text-xs font-mono text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded">{item.name}</code></td>
                <td className="td font-medium text-gray-900 text-sm">{item.display_name}</td>
                <td className="td text-gray-500 text-xs truncate max-w-[280px]">{item.description || "—"}</td>
              </tr>
            ))}
            {items.length === 0 && <tr><td colSpan={3} className="td text-center py-16 text-gray-400 text-sm">No items.</td></tr>}
          </tbody>
        </table>
      </div>

      {total > 30 && (
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Page {page} · {total} total</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1,p-1))} disabled={page===1} className="btn-secondary btn-sm disabled:opacity-40">Prev</button>
            <button onClick={() => setPage(p => p+1)} disabled={items.length<30} className="btn-secondary btn-sm disabled:opacity-40">Next</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Catalog;
