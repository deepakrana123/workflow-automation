import { Link } from "react-router-dom";
import { useGetWorkflowsQuery } from "@/store/api";
import StatusBadge from "@/components/StatusBadge";
import { Plus, GitBranch } from "lucide-react";

const Workflows = () => {
  const { data: workflows = [], isLoading } = useGetWorkflowsQuery();

  return (
    <div className="animate-in space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Workflows</h1>
          <p className="text-sm text-gray-500 mt-0.5">{workflows.length} total</p>
        </div>
        <Link to="/workflows/generate" className="btn-brand"><Plus size={14} /> New</Link>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead><tr className="border-b border-gray-100 bg-gray-50/50">
            <th className="th">Name</th><th className="th">Domain</th><th className="th">Status</th><th className="th">Created</th>
          </tr></thead>
          <tbody>
            {workflows.map((wf: any) => (
              <tr key={wf.id} className="tr">
                <td className="td">
                  <Link to={`/workflows/${wf.id}`} className="flex items-center gap-2 text-sm font-medium text-gray-900 hover:text-brand-600">
                    <div className="w-6 h-6 rounded bg-gray-100 flex items-center justify-center"><GitBranch size={12} className="text-gray-500" /></div>
                    {wf.name}
                  </Link>
                </td>
                <td className="td"><span className="badge bg-gray-100 text-gray-600">{wf.domain}</span></td>
                <td className="td"><StatusBadge status={wf.status || "active"} /></td>
                <td className="td text-gray-500 text-xs">{new Date(wf.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}</td>
              </tr>
            ))}
            {!isLoading && workflows.length === 0 && (
              <tr><td colSpan={4} className="td text-center py-16 text-gray-400 text-sm">
                <GitBranch size={20} className="mx-auto mb-2 text-gray-300" />
                No workflows yet
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Workflows;
