import { NavLink } from "react-router-dom";

const tabs = [
  { to: "/dashboard", label: "風險總覽" },
  { to: "/verify", label: "快速查證" },
  { to: "/alerts", label: "追蹤提醒" },
  { to: "/history", label: "分析紀錄" },
];

export function TopNav() {
  return (
    <nav className="flex items-center gap-1">
      {tabs.map((tab) => (
        <NavLink
          key={tab.to}
          to={tab.to}
          className={({ isActive }) =>
            `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              isActive
                ? "bg-brand-blue text-white"
                : "text-slate-200 hover:bg-white/10 hover:text-white"
            }`
          }
        >
          {tab.label}
        </NavLink>
      ))}
    </nav>
  );
}
