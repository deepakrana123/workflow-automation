import { useState } from "react";
import { Outlet, NavLink } from "react-router-dom";
import {
  FolderKanban,
  GitBranch,
  Play,
  CheckSquare,
  LayoutDashboard,
  Search,
  Activity,
  BarChart3,
  ChevronDown,
  ChevronRight,
  Bell,
} from "lucide-react";
import { clsx } from "clsx";

const primary = [
  { to: "/",           label: "Dashboard",   icon: LayoutDashboard },
  { to: "/workspaces", label: "Workspaces",  icon: FolderKanban },
  { to: "/workflows",  label: "Workflows",   icon: GitBranch },
  { to: "/executions", label: "Executions",  icon: Play },
  { to: "/human-tasks",label: "Tasks",       icon: CheckSquare },
];

const secondary = [
  { to: "/catalog",    label: "Catalog",     icon: Search },
  { to: "/traces",     label: "Traces",      icon: Activity },
  { to: "/analytics",  label: "Analytics",   icon: BarChart3 },
];

const Layout = () => {
  const [showMore, setShowMore] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* ─── Sidebar ─── */}
      <aside className="w-[200px] bg-white border-r border-gray-200 flex flex-col shrink-0">
        {/* Brand */}
        <div className="h-14 flex items-center gap-2.5 px-5 border-b border-gray-100">
          <div className="w-7 h-7 rounded-lg bg-gray-900 flex items-center justify-center">
            <span className="text-white font-bold text-xs">M</span>
          </div>
          <span className="font-semibold text-sm text-gray-900">MFlows</span>
        </div>

        {/* Primary nav */}
        <nav className="flex-1 py-3 px-3 space-y-0.5 overflow-y-auto">
          {primary.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-2.5 px-2.5 py-[7px] rounded-lg text-[13px] font-medium transition-colors",
                  isActive
                    ? "bg-gray-100 text-gray-900"
                    : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
                )
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon size={15} strokeWidth={isActive ? 2.2 : 1.8} className="shrink-0" />
                  <span>{item.label}</span>
                </>
              )}
            </NavLink>
          ))}

          {/* Secondary — collapsible */}
          <div className="pt-2">
            <button
              onClick={() => setShowMore((v) => !v)}
              className="w-full flex items-center gap-1.5 px-2.5 py-1.5 text-[11px] font-semibold text-gray-400 uppercase tracking-widest hover:text-gray-600 transition-colors"
            >
              {showMore ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
              Tools
            </button>
            {showMore && (
              <div className="space-y-0.5 mt-0.5">
                {secondary.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      clsx(
                        "flex items-center gap-2.5 px-2.5 py-[7px] rounded-lg text-[13px] font-medium transition-colors",
                        isActive
                          ? "bg-gray-100 text-gray-900"
                          : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
                      )
                    }
                  >
                    {({ isActive }) => (
                      <>
                        <item.icon size={15} strokeWidth={isActive ? 2.2 : 1.8} className="shrink-0" />
                        <span>{item.label}</span>
                      </>
                    )}
                  </NavLink>
                ))}
              </div>
            )}
          </div>
        </nav>

        {/* User */}
        <div className="px-3 py-3 border-t border-gray-100">
          <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
            <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center shrink-0">
              <span className="text-gray-600 font-semibold text-[10px]">DT</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-900 truncate">Dev Team</p>
            </div>
            <ChevronDown size={11} className="text-gray-400 shrink-0" />
          </div>
        </div>
      </aside>

      {/* ─── Main ─── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
          <div />
          <div className="flex items-center gap-3">
            <button className="relative p-2 rounded-lg hover:bg-gray-100 text-gray-400 transition-colors">
              <Bell size={15} />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-blue-500 rounded-full" />
            </button>
            <span className="text-[11px] text-gray-300 font-medium">v2.0</span>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto">
          <div className="max-w-[1100px] mx-auto px-6 py-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
