import { Outlet } from "react-router-dom";
import { TopNav } from "./TopNav";
import { SidebarMenu } from "./SidebarMenu";
import { brand } from "../../content/copy";

export function AppShell() {
  return (
    <div className="min-h-screen bg-brand-surface">
      <header className="bg-brand-navy shadow-md">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-3">
          <div className="flex items-center gap-8">
            <span className="text-lg font-semibold text-white">{brand.name}</span>
            <TopNav />
          </div>
          <SidebarMenu />
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
