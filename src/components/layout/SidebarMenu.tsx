import { NavLink } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export function SidebarMenu() {
  const { user, logout } = useAuth();

  return (
    <div className="flex items-center gap-3 text-sm">
      <NavLink
        to="/about"
        className={({ isActive }) =>
          `rounded-md px-2 py-1 transition-colors ${
            isActive ? "text-white" : "text-slate-300 hover:text-white"
          }`
        }
      >
        系統說明
      </NavLink>
      <NavLink
        to="/settings"
        className={({ isActive }) =>
          `rounded-md px-2 py-1 transition-colors ${
            isActive ? "text-white" : "text-slate-300 hover:text-white"
          }`
        }
      >
        會員設定
      </NavLink>
      <span className="hidden text-slate-400 sm:inline">{user?.email}</span>
      <button
        onClick={logout}
        className="rounded-md border border-white/20 px-2.5 py-1 text-slate-200 hover:bg-white/10 hover:text-white"
      >
        登出
      </button>
    </div>
  );
}
