import { Outlet, NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  GitBranch,
  Play,
  Search,
  FileUp,
  BarChart3,
  Activity,
  Sparkles,
  Plug,
  Settings,
  Heart,
} from "lucide-react";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/workflows", label: "Workflows", icon: GitBranch },
  { to: "/executions", label: "Executions", icon: Play },
  { to: "/catalog", label: "Catalog", icon: Search },
  { to: "/knowledge", label: "BRD Ingestion", icon: FileUp },
  { to: "/traces", label: "Traces", icon: Activity },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/prompts", label: "Prompts", icon: Sparkles },
  { to: "/integrations", label: "Integrations", icon: Plug },
  { to: "/configurations", label: "Configurations", icon: Settings },
  { to: "/settings", label: "Health", icon: Heart },
];

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="w-56 bg-brand-900 text-white flex flex-col shrink-0">
        <div className="px-5 py-5 border-b border-white/10">
          <h1 className="text-lg font-bold tracking-tight">MFlows</h1>
          <p className="text-xs text-white/50 mt-0.5">Banking Workflows</p>
        </div>
        <nav className="flex-1 py-4 space-y-0.5 px-3 overflow-y-auto">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-white/10 text-white"
                    : "text-white/60 hover:text-white hover:bg-white/5"
                }`
              }
            >
              <item.icon size={16} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-white/10 text-xs text-white/40">
          v2.0.0
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto bg-gray-50">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
