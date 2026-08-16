import { useState } from "react";
import { Link } from "react-router-dom";
import { useGetWorkspacesQuery, useCreateWorkspaceMutation } from "@/store/api";
import { FolderKanban, Plus } from "lucide-react";

const Workspaces = () => {
  const { data: workspaces } = useGetWorkspacesQuery();
  const [create, { isLoading, error }] = useCreateWorkspaceMutation();
  const [form, setForm] = useState({ name: "", display_name: "", organization_name: "" });
  const errorMsg = (error as any)?.data?.detail || "";

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name || !form.display_name) return;
    create(form).then(() => setForm({ name: "", display_name: "", organization_name: "" }));
  };

  return (
    <div className="animate-in space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Workspaces</h1>
        <p className="text-sm text-gray-500 mt-0.5">Each workspace is one banking project</p>
      </div>

      <form onSubmit={handleCreate} className="card p-4 flex flex-wrap gap-2 items-end">
        <div className="flex-1 min-w-[140px]">
          <label className="text-2xs text-gray-500">Name (slug)</label>
          <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="loan_origination" />
        </div>
        <div className="flex-1 min-w-[140px]">
          <label className="text-2xs text-gray-500">Display name</label>
          <input className="input" value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} placeholder="Loan Origination" />
        </div>
        <div className="flex-1 min-w-[140px]">
          <label className="text-2xs text-gray-500">Organization</label>
          <input className="input" value={form.organization_name} onChange={(e) => setForm({ ...form, organization_name: e.target.value })} placeholder="Acme Bank" />
        </div>
        <button className="btn-brand" disabled={isLoading}><Plus size={14} /> Create</button>
      </form>
      {errorMsg && <div className="card border-red-200 bg-red-50 p-3 text-sm text-danger">{errorMsg}</div>}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {(workspaces || []).map((w: any) => (
          <Link key={w.id} to={`/workspaces/${w.id}`} className="card p-4 hover:border-brand-300 transition-colors">
            <div className="flex items-center gap-2">
              <FolderKanban size={16} className="text-brand-600" />
              <span className="font-medium text-gray-900 text-sm">{w.display_name}</span>
            </div>
            <p className="text-2xs text-gray-400 mt-1">{w.name}</p>
            {w.organization_name && <p className="text-xs text-gray-500 mt-1">{w.organization_name}</p>}
          </Link>
        ))}
        {(!workspaces || workspaces.length === 0) && (
          <div className="card p-8 text-center text-sm text-gray-400 col-span-full">No workspaces yet.</div>
        )}
      </div>
    </div>
  );
};

export default Workspaces;
