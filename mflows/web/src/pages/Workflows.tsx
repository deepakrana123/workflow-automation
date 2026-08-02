import { Link } from "react-router-dom";
import { useGetWorkflowsQuery } from "@/store/api";
import StatusBadge from "@/components/StatusBadge";
import { Plus } from "lucide-react";

export default function Workflows() {
  const { data: workflows = [], isLoading } = useGetWorkflowsQuery();

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Workflows</h1>
        <Link
          to="/workflows/generate"
          className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 transition-colors"
        >
          <Plus size={16} />
          Generate Workflow
        </Link>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Domain</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {workflows.map((wf: any) => (
              <tr key={wf.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 font-medium text-gray-900">{wf.name}</td>
                <td className="px-4 py-3 text-gray-600">{wf.domain}</td>
                <td className="px-4 py-3"><StatusBadge status={wf.status || "active"} /></td>
                <td className="px-4 py-3 text-gray-500">
                  {new Date(wf.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
            {!isLoading && workflows.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-12 text-center text-gray-400">
                  No workflows yet. Generate your first one.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
