import { useState } from "react";
import { Link } from "react-router-dom";
import { RegisterForm } from "../components/auth/RegisterForm";
import { RegisterConfirmation } from "../components/auth/RegisterConfirmation";
import { brand } from "../content/copy";

export function RegisterPage() {
  const [isDone, setIsDone] = useState(false);

  return (
    <div className="flex min-h-screen items-center justify-center bg-brand-navy px-4 py-10">
      <div className="w-full max-w-2xl rounded-2xl bg-white p-8 shadow-xl">
        <p className="text-sm font-semibold text-brand-blue">{brand.name}</p>
        <h1 className="mt-2 text-2xl font-bold text-brand-navy">建立帳號並設定追蹤內容</h1>
        <p className="mt-2 text-sm leading-relaxed text-brand-muted">
          設定投資經驗、關注市場與追蹤標的，系統會依照你的設定提供可信度風險提醒，非投資建議。
        </p>
        <div className="mt-6">
          {isDone ? (
            <RegisterConfirmation />
          ) : (
            <RegisterForm onSuccess={() => setIsDone(true)} />
          )}
        </div>
        {!isDone && (
          <p className="mt-6 text-center text-sm text-brand-muted">
            已經有帳號？{" "}
            <Link to="/login" className="font-medium text-brand-blue hover:underline">
              前往登入
            </Link>
          </p>
        )}
      </div>
    </div>
  );
}
