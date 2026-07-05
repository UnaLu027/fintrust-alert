import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <h1 className="text-3xl font-bold text-brand-navy">404</h1>
      <p className="text-sm text-brand-muted">找不到此頁面</p>
      <Link to="/dashboard" className="text-sm font-medium text-brand-blue hover:underline">
        返回風險總覽
      </Link>
    </div>
  );
}
