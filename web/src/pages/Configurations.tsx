import { useState } from "react";
import { useGetConfigurationsQuery, useUpdateConfigurationMutation, useActivateConfigurationMutation, useDeactivateConfigurationMutation } from "@/store/api";
import { Wrench, ToggleLeft, ToggleRight } from "lucide-react";
import { Modal } from "@/components/shared/Modal";
import { FormRenderer } from "@/components/shared/FormRenderer";
import { Input } from "@/components/shared/Input";
import { Badge } from "@/components/shared/Badge";
import { EmptyState } from "@/components/shared/EmptyState";
import { CONFIGURATION_EDIT_FIELDS } from "@/config/forms";

const Configurations = () => {
  const [workflowId, setWorkflowId] = useState(1);
  const { data: configs = [] } = useGetConfigurationsQuery(workflowId);
  const [update] = useUpdateConfigurationMutation();
  const [activate] = useActivateConfigurationMutation();
  const [deactivate] = useDeactivateConfigurationMutation();
  const [editId, setEditId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<Record<string, unknown>>({});

  const openEdit = (c: any) => {
    setEditId(c.id);
    setEditForm({
      execution_type: c.execution_type,
      configuration: JSON.stringify(c.configuration || {}, null, 2),
      workspace_integration_id: c.workspace_integration_id || "",
    });
  };

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editId) return;
    let cfg = {};
    try { cfg = JSON.parse(editForm.configuration as string); } catch { return; }
    update({
      id: editId,
      body: {
        execution_type: editForm.execution_type,
        configuration: cfg,
        workspace_integration_id: editForm.workspace_integration_id
          ? Number(editForm.workspace_integration_id)
          : null,
      },
    });
    setEditId(null);
  };

  return (
    <div className="animate-in space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Configurations</h1>
          <p className="text-sm text-gray-500 mt-0.5">Action execution config</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Knowledge ID:</span>
          <Input
            type="number"
            value={workflowId}
            onChange={(e) => setWorkflowId(Number(e.target.value) || 1)}
            className="w-16 h-7 text-center text-xs"
          />
        </div>
      </div>

      {/* Edit Modal */}
      <Modal open={!!editId} onClose={() => setEditId(null)} title={`Edit #${editId}`}>
        <FormRenderer
          fields={CONFIGURATION_EDIT_FIELDS}
          values={editForm}
          onChange={setEditForm}
          onSubmit={handleUpdate}
          submitLabel="Save"
          onCancel={() => setEditId(null)}
        />
      </Modal>

      {/* Table */}
      <div className="card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50/50">
              <th className="th">ID</th>
              <th className="th">Action</th>
              <th className="th">Type</th>
              <th className="th">Ver</th>
              <th className="th">Active</th>
              <th className="th"></th>
            </tr>
          </thead>
          <tbody>
            {configs.map((c: any) => (
              <tr key={c.id} className="tr">
                <td className="td text-gray-400 font-mono text-xs">{c.id}</td>
                <td className="td text-gray-900 text-sm">{c.action_definition_id}</td>
                <td className="td"><Badge>{c.execution_type}</Badge></td>
                <td className="td text-gray-500 text-xs">v{c.version}</td>
                <td className="td">
                  {c.active ? (
                    <button onClick={() => deactivate(c.id)} className="text-success hover:text-danger transition-colors">
                      <ToggleRight size={18} />
                    </button>
                  ) : (
                    <button onClick={() => activate(c.id)} className="text-gray-300 hover:text-success transition-colors">
                      <ToggleLeft size={18} />
                    </button>
                  )}
                </td>
                <td className="td">
                  <button onClick={() => openEdit(c)} className="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-700">
                    <Wrench size={13} />
                  </button>
                </td>
              </tr>
            ))}
            {configs.length === 0 && (
              <tr>
                <td colSpan={6}>
                  <EmptyState icon={Wrench} title="No configurations" />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Configurations;
