import { useGetHealthQuery } from "@/store/api";
import { CheckCircle2, XCircle, RefreshCw } from "lucide-react";

const Settings = () => {
  const { data: health, refetch, isFetching } = useGetHealthQuery();

  return (
    <div className="animate-in space-y-5 max-w-lg">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">System Health</h1>
          <p className="text-sm text-gray-500 mt-0.5">Service checks</p>
        </div>
        <button onClick={() => refetch()} className="btn-secondary btn-sm">
          <RefreshCw size={12} className={isFetching ? "animate-spin" : ""} /> Check
        </button>
      </div>

      <div className="space-y-2">
        {health?.checks && Object.entries(health.checks).map(([name, check]: [string, any]) => (
          <div key={name} className="card p-4 flex items-center gap-3">
            {check.status === "ok"
              ? <CheckCircle2 size={16} className="text-success shrink-0" />
              : <XCircle size={16} className="text-danger shrink-0" />}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 capitalize">{name.replace(/_/g, " ")}</p>
              {check.error && <p className="text-2xs text-danger mt-0.5 truncate">{check.error}</p>}
            </div>
            <span className={`badge ${check.status === "ok" ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>{check.status}</span>
          </div>
        ))}
        {!health && <div className="card p-12 text-center text-gray-400 text-sm">Loading...</div>}
      </div>
    </div>
  );
}

export default Settings;
