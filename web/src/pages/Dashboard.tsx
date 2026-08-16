import { useGetDashboardStatsQuery, useGetExecutionTrendQuery } from "@/store/api";
import KPICard from "@/components/KPICard";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { GitBranch, Play, TrendingUp, Layers, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

const Dashboard = () => {
  const { data: stats } = useGetDashboardStatsQuery();
  const { data: trend } = useGetExecutionTrendQuery(7);

  return (
    <div className="animate-in space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-0.5">Workflow platform overview</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KPICard title="Workflows" value={stats?.total_workflows ?? "—"} icon={GitBranch} trend="up" trendValue="12%" subtitle="this week" />
        <KPICard title="Executions" value={stats?.total_executions ?? "—"} icon={Play} trend="up" trendValue="8%" subtitle="vs last" />
        <KPICard title="Success Rate" value={stats ? `${(stats.success_rate * 100).toFixed(1)}%` : "—"} icon={TrendingUp} trend="up" trendValue="2.1%" />
        <KPICard title="Queue Depth" value={stats?.queue_depth ?? "—"} icon={Layers} subtitle="active now" />
      </div>

      {/* Chart */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-semibold text-gray-900">Execution Trend</h2>
            <p className="text-2xs text-gray-400 mt-0.5">Last 7 days</p>
          </div>
          <div className="flex items-center gap-4 text-2xs text-gray-500">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-success" />Success</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-danger" />Failed</span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={trend || []}>
            <defs>
              <linearGradient id="gs" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity={0.08} />
                <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gf" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ef4444" stopOpacity={0.08} />
                <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#f4f4f5" vertical={false} />
            <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#a1a1aa" }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: "#a1a1aa" }} axisLine={false} tickLine={false} width={32} />
            <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #e4e4e7", boxShadow: "0 2px 8px rgb(0 0 0 / 0.05)" }} />
            <Area type="monotone" dataKey="success" stroke="#10b981" strokeWidth={1.5} fill="url(#gs)" dot={false} />
            <Area type="monotone" dataKey="failed" stroke="#ef4444" strokeWidth={1.5} fill="url(#gf)" dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Global generation disabled — workflows are workspace-scoped now.
        <Link to="/workflows/generate" className="card p-4 flex items-center gap-3 ...">
          Generate Workflow (global catalog)
        </Link>
        */}
        <Link to="/workspaces" className="card p-4 flex items-center gap-3 hover:shadow-card transition-shadow group">
          <div className="w-9 h-9 rounded-lg bg-brand-50 flex items-center justify-center group-hover:bg-brand-100 transition-colors">
            <GitBranch size={16} className="text-brand-600" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-900">Build a Workflow</p>
            <p className="text-2xs text-gray-400">Select a workspace → AI generation</p>
          </div>
          <ArrowRight size={14} className="text-gray-300 group-hover:text-gray-500 transition-colors" />
        </Link>
        <Link to="/knowledge" className="card p-4 flex items-center gap-3 hover:shadow-card transition-shadow group">
          <div className="w-9 h-9 rounded-lg bg-purple-50 flex items-center justify-center group-hover:bg-purple-100 transition-colors">
            <Play size={16} className="text-purple-600" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-900">Upload BRD</p>
            <p className="text-2xs text-gray-400">Extract workflow knowledge</p>
          </div>
          <ArrowRight size={14} className="text-gray-300 group-hover:text-gray-500 transition-colors" />
        </Link>
      </div>
    </div>
  );
}

export default Dashboard;
