import { useState } from "react";
import { useGetTriggersQuery, useGetActionsQuery } from "@/store/api";
import { Search, Zap, Play } from "lucide-react";
import { clsx } from "clsx";

// Colour map for workflow_type badges — falls back to gray for unknown types
const TYPE_COLORS: Record<string, string> = {
  finance:     "bg-blue-50 text-blue-700",
  health:      "bg-green-50 text-green-700",
  support:     "bg-orange-50 text-orange-700",
  insurance:   "bg-purple-50 text-purple-700",
  collections: "bg-red-50 text-red-700",
  hr:          "bg-pink-50 text-pink-700",
  logistics:   "bg-cyan-50 text-cyan-700",
};

const typeBadge = (wt: string) => (
  <span className={clsx(
    "inline-block px-1.5 py-0.5 rounded text-[10px] font-medium capitalize",
    TYPE_COLORS[wt?.toLowerCase()] ?? "bg-gray-100 text-gray-500",
  )}>
    {wt || "—"}
  </span>
);

// execution_type badge — actions only
const execBadge = (tpl: any) => {
  if (!tpl?.execution_type) return null;
  const et: string = tpl.execution_type;
  const colours: Record<string, string> = {
    python:     "bg-yellow-50 text-yellow-700",
    http:       "bg-sky-50 text-sky-700",
    human_task: "bg-violet-50 text-violet-700",
  };
  return (
    <span className={clsx(
      "inline-block px-1.5 py-0.5 rounded text-[10px] font-medium",
      colours[et] ?? "bg-gray-100 text-gray-500",
    )}>
      {et}
    </span>
  );
};

const Catalog = () => {
  const [tab, setTab]       = useState<"actions" | "triggers">("actions");
  const [search, setSearch] = useState("");
  const [page, setPage]     = useState(1);

  const triggerQuery = useGetTriggersQuery(
    { page, page_size: 30, search },
    { skip: tab !== "triggers" },
  );
  const actionQuery = useGetActionsQuery(
    { page, page_size: 30, search },
    { skip: tab !== "actions" },
  );

  const data    = tab === "triggers" ? triggerQuery.data : actionQuery.data;
  const loading = tab === "triggers" ? triggerQuery.isLoading : actionQuery.isLoading;
  const items   = data?.data  || [];
  const total   = data?.total || 0;

  return (
    <div className="animate-in space-y-5">

      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Catalog</h1>
          <p className="text-sm text-gray-500 mt-0.5">Triggers &amp; actions available for workflow generation</p>
        </div>
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search…"
            className="input pl-9 w-56"
          />
        </div>
      </div>

      {/* ── Tab bar ── */}
      <div className="flex gap-1 p-1 bg-gray-100 rounded-lg w-fit">
        {(["actions", "triggers"] as const).map((t) => (
          <button
            key={t}
            onClick={() => { setTab(t); setPage(1); setSearch(""); }}
            className={clsx(
              "flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md capitalize transition-all",
              tab === t ? "bg-white text-gray-900 shadow-xs" : "text-gray-500 hover:text-gray-700",
            )}
          >
            {t === "actions"
              ? <Play size={11} className="shrink-0" />
              : <Zap  size={11} className="shrink-0" />}
            {t}
            {tab === t && <span className="text-gray-400 font-normal">({total})</span>}
          </button>
        ))}
      </div>

      {/* ── Table ── */}
      <div className="card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50/50">
              <th className="th w-56">Name</th>
              <th className="th w-44">Display Name</th>
              <th className="th">Description</th>
              <th className="th w-28">Type</th>
              {tab === "actions" && <th className="th w-24">Executor</th>}
              <th className="th w-44">Aliases</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={tab === "actions" ? 6 : 5} className="td text-center py-16 text-gray-400 text-sm">
                  Loading…
                </td>
              </tr>
            )}

            {!loading && items.map((item: any) => (
              <tr key={item.id} className="tr">

                {/* name */}
                <td className="td">
                  <code className="text-xs font-mono text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded">
                    {item.name}
                  </code>
                </td>

                {/* display_name */}
                <td className="td font-medium text-gray-900 text-sm">
                  {item.display_name}
                </td>

                {/* description */}
                <td className="td text-gray-500 text-xs max-w-[260px]">
                  <span className="line-clamp-2">{item.description || "—"}</span>
                </td>

                {/* workflow_type */}
                <td className="td">{typeBadge(item.workflow_type)}</td>

                {/* execution_type — actions only */}
                {tab === "actions" && (
                  <td className="td">{execBadge(item.execution_template) ?? <span className="text-gray-300 text-xs">—</span>}</td>
                )}

                {/* aliases */}
                <td className="td">
                  {item.aliases?.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {item.aliases.slice(0, 3).map((a: string) => (
                        <span key={a} className="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">
                          {a}
                        </span>
                      ))}
                      {item.aliases.length > 3 && (
                        <span className="text-[10px] text-gray-400">+{item.aliases.length - 3}</span>
                      )}
                    </div>
                  ) : (
                    <span className="text-gray-300 text-xs">—</span>
                  )}
                </td>

              </tr>
            ))}

            {!loading && items.length === 0 && (
              <tr>
                <td colSpan={tab === "actions" ? 6 : 5} className="td text-center py-16 text-gray-400 text-sm">
                  No {tab} found{search ? ` matching "${search}"` : ""}.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* ── Pagination ── */}
      {total > 30 && (
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Page {page} · {total} total</span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn-secondary btn-sm disabled:opacity-40"
            >
              Prev
            </button>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={items.length < 30}
              className="btn-secondary btn-sm disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}

    </div>
  );
};

export default Catalog;
