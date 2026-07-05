import { Link } from "react-router-dom";
import { LoginForm } from "../components/auth/LoginForm";
import { authCopy, brand } from "../content/copy";

export function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-brand-navy px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl">
        <p className="text-sm font-semibold text-brand-blue">{brand.name}</p>
        <h1 className="mt-2 text-2xl font-bold text-brand-navy">{authCopy.loginTitle}</h1>
        <p className="mt-2 text-sm leading-relaxed text-brand-muted">{authCopy.loginSubtitle}</p>
        <div className="mt-6">
          <LoginForm />
        </div>
        <p className="mt-6 text-center text-sm text-brand-muted">
          還沒有帳號？{" "}
          <Link to="/register" className="font-medium text-brand-blue hover:underline">
            立即註冊
          </Link>
        </p>
      </div>
    </div>
  );
}
