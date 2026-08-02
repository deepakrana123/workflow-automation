import { useState } from "react";
import { useGetConfigurationsQuery, useUpdateConfigurationMutation, useActivateConfigurationMutation, useDeactivateConfigurationMutation } from "@/store/api";
import { Settings, ToggleLeft, ToggleRight } from "lucide-react";

export default function Configurations() {
  const [workflowId, setWorkflowId] = useState(1);
  const { data: configs = [] } = useGetConfigurationsQuery(workflowId);
  const [update] = useUpdateConfigurationMutation();
  const [activate] = useActivateConfigurationMutation();
  const [deactivate] = useDeactivateConfigurationMutation();
  const [editId, setEditId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState({ execution_type: "python", configuration: "{}", workspace_integration_id: "" });

  function openEdit(config: any) {
    setEditId(config.id);
    setEditForm({
      execution_type: config.execution_type,
      configuration: JSON.stringify(config.configuration || {}, null, 2),
      workspace_integration_id: config.workspace_integration_id || "",
    });
  }

  function handleUpdate(e: React.FormEvent) {
    e.preventDefault();
    if (!editId) return;
    let cfg = {};
    try { cfg = JSON.parse(editForm.configuration); } catch { return; }
    update({
      id: editId,
      body: {
        execution_type: editForm.execution_type,
        configuration: cfg,
        workspace_integration_id: editForm.workspace_integration_id ? Number(editForm.workspace_integration_id) : null,
      },
    });
    setEditId(null);
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Action Configurations</h1>

      <div className="mb-4">
        <label className="text-xs font-medium text-gray-600 mr-2">Workflow Knowledge ID:</label>
        <input
          type="number"
          value={workflowId}
          onChange={(e) => setWorkflowId(Number(e.target.value) || 1)}
          className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm w-24 outline-none focus:ring-2 focus:ring-brand-500"
        />
      </div>

      {/* Edit modal */}
      {editId && (
        <form onSubmit={handleUpdate} className="bg-white border border-gray-200 rounded-xl p-6 mb-6 space-y-4">
          <h3 className="text-sm font-semibold text-gray-700">Edit Configuration #{editId}</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Execution Type</label>
              <select value={editForm.execution_type} onChange={(e) => setEditForm({ ...editForm, execution_type: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none">
                <option value="python">Python</option>
                <option value="http">HTTP</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Workspace Integration ID</label>
              <input value={editForm.workspace_integration_id} onChange={(e) => setEditForm({ ...editForm, workspace_integration_id: e.target.value })} placeholder="(optional for HTTP)" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none" />
            </div>
            <div className="col-span-2">
              <label className="block text-xs font-medium text-gray-600 mb-1">Configuration (JSON)</label>
              <textarea value={editForm.configuration} onChange={(e) => setEditForm({ ...editForm, configuration: e.target.value })} rows={5} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono outline-none focus:ring-2 focus:ring-brand-500" />
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" className="px-4 py-2 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700">Save New Version</button>
            <button type="button" onClick={() => setEditId(null)} className="px-4 py-2 border border-gray-300 text-gray-600 text-sm rounded-lg hover:bg-gray-50">Cancel</button>
          </div>
        </form>
      )}

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Action Def</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Type</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Version</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Active</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {configs.map((c: any) => (
              <tr key={c.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-gray-800 font-mono text-xs">{c.id}</td>
                <td className="px-4 py-3 text-gray-700">{c.action_definition_id}</td>
                <td className="px-4 py-3"><span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs font-medium">{c.execution_type}</span></td>
                <td className="px-4 py-3 text-gray-500">v{c.version}</td>
                <td className="px-4 py-3">
                  {c.active ? (
                    <button onClick={() => deactivate(c.id)} className="text-emerald-600 hover:text-red-500"><ToggleRight size={20} /></button>
                  ) : (
                    <button onClick={() => activate(c.id)} className="text-gray-400 hover:text-emerald-600"><ToggleLeft size={20} /></button>
                  )}
                </td>
                <td className="px-4 py-3">
                  <button onClick={() => openEdit(c)} className="text-gray-400 hover:text-brand-600"><Settings size={16} /></button>
                </td>
              </tr>
            ))}
            {configs.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-12 text-center text-gray-400">No configurations for this workflow.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
