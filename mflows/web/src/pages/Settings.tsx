import { useGetHealthQuery } from "@/store/api";
import { CheckCircle2, XCircle, RefreshCw } from "lucide-react";

export default function Settings() {
  const { data: health, refetch, isFetching } = useGetHealthQuery();

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">System Health</h1>
        <button onClick={() => refetch()} className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium border border-gray-300 rounded-lg hover:bg-gray-50">
          <RefreshCw size={14} className={isFetching ? "animate-spin" : ""} /> Check
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {health?.checks && Object.entries(health.checks).map(([name, check]: [string, any]) => (
          <div key={name} className="bg-white border border-gray-200 rounded-xl p-5 flex items-center gap-4">
            {check.status === "ok" ? (
              <CheckCircle2 className="text-emerald-500" size={24} />
            ) : (
              <XCircle className="text-red-500" size={24} />
            )}
            <div className="flex-1">
              <p className="font-medium text-gray-900 capitalize">{name.replace(/_/g, " ")}</p>
              {check.error && <p className="text-xs text-red-500 mt-0.5">{check.error}</p>}
            </div>
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${check.status === "ok" ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
              {check.status}
            </span>
          </div>
        ))}
        {!health && (
          <p className="text-gray-400 text-sm">Loading health status...</p>
        )}
      </div>
    </div>
  );
}
