import { useState } from "react";
import { useGetIntegrationsQuery, useCreateIntegrationMutation, useDeleteIntegrationMutation } from "@/store/api";
import { Plus, Plug, Trash2, MoreHorizontal } from "lucide-react";
import { Modal } from "@/components/shared/Modal";
import { FormRenderer } from "@/components/shared/FormRenderer";
import { Dropdown } from "@/components/shared/Dropdown";
import { EmptyState } from "@/components/shared/EmptyState";
import { Badge } from "@/components/shared/Badge";
import { INTEGRATION_FIELDS, INTEGRATION_DEFAULTS } from "@/config/forms";

const Integrations = () => {
  const { data: integrations = [] } = useGetIntegrationsQuery(1);
  const [create] = useCreateIntegrationMutation();
  const [remove] = useDeleteIntegrationMutation();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<Record<string, unknown>>({ ...INTEGRATION_DEFAULTS });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    let creds = {};
    try { creds = JSON.parse(form.credentials as string); } catch { /* */ }
    create({ workspaceId: 1, body: { ...form, credentials: creds } });
    setShowCreate(false);
    setForm({ ...INTEGRATION_DEFAULTS });
  };

  const handleDelete = (id: number) => {
    remove(id);
  };

  return (
    <div className="animate-in space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Integrations</h1>
          <p className="text-sm text-gray-500 mt-0.5">{integrations.length} connected</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-brand">
          <Plus size={14} /> Add
        </button>
      </div>

      {/* Create Modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="New Integration">
        <FormRenderer
          fields={INTEGRATION_FIELDS}
          values={form}
          onChange={setForm}
          onSubmit={handleCreate}
          submitLabel="Create"
          onCancel={() => setShowCreate(false)}
        />
      </Modal>

      {/* Grid */}
      {integrations.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {integrations.map((i: any) => (
            <IntegrationCard key={i.id} integration={i} onDelete={handleDelete} />
          ))}
        </div>
      ) : (
        <div className="card">
          <EmptyState
            icon={Plug}
            title="No integrations"
            description="Connect your first external service"
            action={<button onClick={() => setShowCreate(true)} className="btn-brand btn-sm">Add integration</button>}
          />
        </div>
      )}
    </div>
  );
};

/* ─── Sub-component ─── */

interface CardProps {
  integration: any;
  onDelete: (id: number) => void;
}

const IntegrationCard = ({ integration: i, onDelete }: CardProps) => (
  <div className="card p-4 group hover:shadow-card transition-shadow">
    <div className="flex items-start justify-between mb-3">
      <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center">
        <Plug size={14} className="text-gray-500" />
      </div>
      <Dropdown
        trigger={
          <button className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-gray-100 text-gray-400 transition-all">
            <MoreHorizontal size={14} />
          </button>
        }
        items={[
          { label: "Delete", onClick: () => onDelete(i.id), danger: true, icon: <Trash2 size={12} /> },
        ]}
      />
    </div>
    <h4 className="text-sm font-medium text-gray-900 mb-1">{i.name}</h4>
    <p className="text-2xs text-gray-400 font-mono truncate mb-2">{i.base_url}</p>
    <div className="flex items-center gap-1.5">
      <Badge>{i.provider_type}</Badge>
      <Badge variant={i.active ? "success" : "default"} dot>{i.active ? "active" : "inactive"}</Badge>
    </div>
  </div>
);

export default Integrations;
