import { useState } from "react";
import { useGetIntegrationsQuery, useCreateIntegrationMutation, useDeleteIntegrationMutation } from "@/store/api";
import { Plus, Trash2 } from "lucide-react";

export default function Integrations() {
  const { data: integrations = [] } = useGetIntegrationsQuery(1); // workspace_id=1
  const [create] = useCreateIntegrationMutation();
  const [remove] = useDeleteIntegrationMutation();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", provider_type: "http", base_url: "", authentication_type: "bearer", credentials: "{}", description: "" });

  function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    let creds = {};
    try { creds = JSON.parse(form.credentials); } catch { /* ignore */ }
    create({ workspaceId: 1, body: { ...form, credentials: creds } });
    setShowForm(false);
    setForm({ name: "", provider_type: "http", base_url: "", authentication_type: "bearer", credentials: "{}", description: "" });
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Workspace Integrations</h1>
        <button onClick={() => setShowForm(!showForm)} className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700">
          <Plus size={16} /> Add Integration
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white border border-gray-200 rounded-xl p-6 mb-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Name</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Provider Type</label>
              <select value={form.provider_type} onChange={(e) => setForm({ ...form, provider_type: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none">
                <option value="http">HTTP</option>
                <option value="soap">SOAP</option>
                <option value="grpc">gRPC</option>
                <option value="kafka">Kafka</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Base URL</label>
              <input value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} required placeholder="https://api.bank.internal" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Auth Type</label>
              <select value={form.authentication_type} onChange={(e) => setForm({ ...form, authentication_type: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none">
                <option value="bearer">Bearer Token</option>
                <option value="api_key">API Key</option>
                <option value="basic">Basic Auth</option>
                <option value="oauth2">OAuth2</option>
              </select>
            </div>
            <div className="col-span-2">
              <label className="block text-xs font-medium text-gray-600 mb-1">Credentials (JSON)</label>
              <textarea value={form.credentials} onChange={(e) => setForm({ ...form, credentials: e.target.value })} rows={2} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono outline-none focus:ring-2 focus:ring-brand-500" />
            </div>
            <div className="col-span-2">
              <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
              <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none" />
            </div>
          </div>
          <button type="submit" className="px-4 py-2 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700">Create</button>
        </form>
      )}

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Provider</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Base URL</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Auth</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Active</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {integrations.map((i: any) => (
              <tr key={i.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{i.name}</td>
                <td className="px-4 py-3 text-gray-600 text-xs uppercase">{i.provider_type}</td>
                <td className="px-4 py-3 text-gray-500 text-xs font-mono truncate max-w-xs">{i.base_url}</td>
                <td className="px-4 py-3 text-gray-500 text-xs">{i.authentication_type}</td>
                <td className="px-4 py-3">{i.active ? <span className="text-emerald-600 text-xs">●</span> : <span className="text-gray-400 text-xs">●</span>}</td>
                <td className="px-4 py-3">
                  <button onClick={() => remove(i.id)} className="text-red-400 hover:text-red-600"><Trash2 size={14} /></button>
                </td>
              </tr>
            ))}
            {integrations.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-12 text-center text-gray-400">No integrations configured.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
