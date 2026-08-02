import { useGetDashboardStatsQuery, useGetExecutionTrendQuery } from "@/store/api";
import KPICard from "@/components/KPICard";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";

export default function Dashboard() {
  const { data: stats } = useGetDashboardStatsQuery();
  const { data: trend } = useGetExecutionTrendQuery(7);

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KPICard title="Total Workflows" value={stats?.total_workflows ?? "—"} />
        <KPICard title="Total Executions" value={stats?.total_executions ?? "—"} />
        <KPICard
          title="Success Rate"
          value={stats ? `${(stats.success_rate * 100).toFixed(1)}%` : "—"}
        />
        <KPICard title="Queue Depth" value={stats?.queue_depth ?? "—"} subtitle="active now" />
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">
          Execution Trend (7 days)
        </h2>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={trend || []}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Line type="monotone" dataKey="success" stroke="#10b981" strokeWidth={2} dot={false} name="Success" />
            <Line type="monotone" dataKey="failed" stroke="#ef4444" strokeWidth={2} dot={false} name="Failed" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
