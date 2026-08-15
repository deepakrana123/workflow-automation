import { Outlet, NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FolderKanban,
  GitBranch,
  Play,
  Search,
  // FileUp, // Ingestion nav removed — upload lives inside workspace Documents tab
  BarChart3,
  Activity,
  Sparkles,
  Plug,
  Wrench,
  Heart,
  Bell,
  ChevronDown,
  CheckSquare,
} from "lucide-react";
import { clsx } from "clsx";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/workspaces", label: "Workspaces", icon: FolderKanban },
  { to: "/workflows", label: "Workflows", icon: GitBranch },
  { to: "/executions", label: "Executions", icon: Play },
  { to: "/human-tasks", label: "Human Tasks", icon: CheckSquare },
  { to: "/catalog", label: "Catalog", icon: Search },
  // { to: "/knowledge", label: "Ingestion", icon: FileUp },
  // BRD upload is now inside each workspace — Workspaces → Documents tab
  { to: "/traces", label: "Traces", icon: Activity },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/prompts", label: "Prompts", icon: Sparkles },
  { to: "/integrations", label: "Integrations", icon: Plug },
  { to: "/configurations", label: "Config", icon: Wrench },
  { to: "/settings", label: "Health", icon: Heart },
];

const Layout = () => {
  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* ─── Sidebar ─── */}
      <aside className="w-[220px] bg-white border-r border-gray-200 flex flex-col shrink-0">
        {/* Brand */}
        <div className="h-14 flex items-center gap-2.5 px-5 border-b border-gray-100">
          <div className="w-7 h-7 rounded-lg bg-gray-900 flex items-center justify-center">
            <span className="text-white font-bold text-xs">M</span>
          </div>
          <span className="font-semibold text-sm text-gray-900">MFlows</span>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3 px-3 space-y-0.5 overflow-y-auto scroll-thin">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-2.5 px-2.5 py-[7px] rounded-lg text-[13px] font-medium transition-colors duration-100",
                  isActive
                    ? "bg-gray-100 text-gray-900"
                    : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
                )
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon size={16} strokeWidth={isActive ? 2.2 : 1.8} className="shrink-0" />
                  <span>{item.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="px-3 py-3 border-t border-gray-100">
          <div className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
            <div className="w-7 h-7 rounded-full bg-brand-100 flex items-center justify-center">
              <span className="text-brand-700 font-semibold text-2xs">DT</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-900 truncate">Dev Team</p>
              <p className="text-2xs text-gray-400 truncate">mflows_bank</p>
            </div>
            <ChevronDown size={12} className="text-gray-400" />
          </div>
        </div>
      </aside>

      {/* ─── Main ─── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
          <div />
          <div className="flex items-center gap-3">
            <button className="relative p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors">
              <Bell size={16} />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-brand-500 rounded-full" />
            </button>
            <div className="w-px h-5 bg-gray-200" />
            <span className="text-2xs text-gray-400 font-medium">v2.0.0</span>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto scroll-thin">
          <div className="max-w-[1120px] mx-auto px-6 py-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}

export default Layout;
