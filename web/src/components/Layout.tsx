import { useState, useEffect } from "react";
import { Outlet, NavLink, useLocation } from "react-router-dom";
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
  Menu,
  X,
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
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  // Close the mobile drawer whenever the route changes.
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    clsx(
      "flex items-center gap-2.5 px-2.5 py-[7px] rounded-lg text-[13px] font-medium transition-colors",
      isActive
        ? "bg-gray-100 text-gray-900"
        : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
    );

  const sidebar = (
    <>
      {/* Brand */}
      <div className="h-14 flex items-center gap-2.5 px-5 border-b border-gray-100 shrink-0">
        <div className="w-7 h-7 rounded-lg bg-gray-900 flex items-center justify-center">
          <span className="text-white font-bold text-xs">M</span>
        </div>
        <span className="font-semibold text-sm text-gray-900">MFlows</span>
        {/* Close button — only visible inside the mobile drawer */}
        <button
          onClick={() => setMobileOpen(false)}
          className="ml-auto p-1.5 rounded-lg hover:bg-gray-100 text-gray-500 md:hidden"
          aria-label="Close menu"
        >
          <X size={16} />
        </button>
      </div>

      {/* Primary nav */}
      <nav className="flex-1 py-3 px-3 space-y-0.5 overflow-y-auto scroll-thin">
        {primary.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.to === "/"} className={navLinkClass}>
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
                <NavLink key={item.to} to={item.to} className={navLinkClass}>
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
      <div className="px-3 py-3 border-t border-gray-100 shrink-0">
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
    </>
  );

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* ─── Sidebar: permanent on md+ ─── */}
      <aside className="hidden md:flex w-[200px] bg-white border-r border-gray-200 flex-col shrink-0">
        {sidebar}
      </aside>

      {/* ─── Sidebar: off-canvas drawer on < md ─── */}
      {/* Backdrop */}
      <div
        className={clsx(
          "fixed inset-0 z-40 bg-black/40 md:hidden transition-opacity duration-200",
          mobileOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onClick={() => setMobileOpen(false)}
        aria-hidden="true"
      />
      {/* Drawer panel */}
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-50 w-[248px] max-w-[80vw] bg-white border-r border-gray-200 flex flex-col md:hidden transition-transform duration-200 ease-out",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {sidebar}
      </aside>

      {/* ─── Main ─── */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4 sm:px-6 shrink-0">
          {/* Hamburger — only on < md */}
          <button
            onClick={() => setMobileOpen(true)}
            className="p-2 -ml-2 rounded-lg hover:bg-gray-100 text-gray-500 md:hidden"
            aria-label="Open menu"
          >
            <Menu size={18} />
          </button>
          <div className="hidden md:block" />
          <div className="flex items-center gap-3">
            <button className="relative p-2 rounded-lg hover:bg-gray-100 text-gray-400 transition-colors">
              <Bell size={15} />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-blue-500 rounded-full" />
            </button>
            <span className="text-[11px] text-gray-300 font-medium">v2.0</span>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto">
          <div className="page-container">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
