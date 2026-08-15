import { useGetExecutionVolumeQuery, useGetFailuresQuery, useGetRetriesQuery, useGetWorkflowCreationQuery } from "@/store/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";

const axis = { fontSize: 10, fill: "#a1a1aa" };
const grid = { stroke: "#f4f4f5", vertical: false } as const;
const tipStyle = { borderRadius: 8, border: "1px solid #e4e4e7", boxShadow: "0 2px 8px rgb(0 0 0 / 0.05)" };

const Analytics = () => {
  const { data: volume = [] } = useGetExecutionVolumeQuery();
  const { data: failures = [] } = useGetFailuresQuery();
  const { data: retries = [] } = useGetRetriesQuery();
  const { data: creation = [] } = useGetWorkflowCreationQuery();

  return (
    <div className="animate-in space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Analytics</h1>
        <p className="text-sm text-gray-500 mt-0.5">Performance metrics</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Chart title="Execution Volume">
          <BarChart data={volume}><CartesianGrid {...grid} /><XAxis dataKey="date" tick={axis} axisLine={false} tickLine={false} /><YAxis tick={axis} axisLine={false} tickLine={false} width={28} /><Tooltip contentStyle={tipStyle} /><Bar dataKey="value" fill="#3b82f6" radius={[3,3,0,0]} /></BarChart>
        </Chart>
        <Chart title="Failure Rate">
          <AreaChart data={failures}><defs><linearGradient id="fa" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#ef4444" stopOpacity={0.08}/><stop offset="100%" stopColor="#ef4444" stopOpacity={0}/></linearGradient></defs><CartesianGrid {...grid} /><XAxis dataKey="date" tick={axis} axisLine={false} tickLine={false} /><YAxis tick={axis} axisLine={false} tickLine={false} width={28} domain={[0,0.5]} /><Tooltip contentStyle={tipStyle} formatter={(v: number) => `${(v*100).toFixed(1)}%`} /><Area type="monotone" dataKey="rate" stroke="#ef4444" strokeWidth={1.5} fill="url(#fa)" dot={false} /></AreaChart>
        </Chart>
        <Chart title="Workflow Creation">
          <AreaChart data={creation}><defs><linearGradient id="ca" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.08}/><stop offset="100%" stopColor="#8b5cf6" stopOpacity={0}/></linearGradient></defs><CartesianGrid {...grid} /><XAxis dataKey="date" tick={axis} axisLine={false} tickLine={false} /><YAxis tick={axis} axisLine={false} tickLine={false} width={28} /><Tooltip contentStyle={tipStyle} /><Area type="monotone" dataKey="value" stroke="#8b5cf6" strokeWidth={1.5} fill="url(#ca)" dot={false} /></AreaChart>
        </Chart>
        <Chart title="Retries">
          <BarChart data={retries}><CartesianGrid {...grid} /><XAxis dataKey="date" tick={axis} axisLine={false} tickLine={false} /><YAxis tick={axis} axisLine={false} tickLine={false} width={28} /><Tooltip contentStyle={tipStyle} /><Bar dataKey="retries" fill="#f59e0b" radius={[3,3,0,0]} /></BarChart>
        </Chart>
      </div>
    </div>
  );
}

const Chart = ({ title, children }: { title: string; children: React.ReactElement }) => {
  return (
    <div className="card p-4">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">{title}</h3>
      <ResponsiveContainer width="100%" height={180}>{children}</ResponsiveContainer>
    </div>
  );
}

export default Analytics;
