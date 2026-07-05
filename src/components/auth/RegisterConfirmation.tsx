import { useNavigate } from "react-router-dom";
import { authCopy } from "../../content/copy";

export function RegisterConfirmation() {
  const navigate = useNavigate();

  return (
    <div className="space-y-6 text-center">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-risk-low-bg text-risk-low">
        ✓
      </div>
      <h2 className="text-xl font-bold text-brand-navy">註冊完成</h2>
      <p className="text-sm leading-relaxed text-brand-muted">{authCopy.registerConfirmation}</p>
      <button
        onClick={() => navigate("/dashboard")}
        className="w-full rounded-md bg-brand-blue py-2.5 text-sm font-semibold text-white hover:bg-brand-navy"
      >
        前往風險總覽
      </button>
    </div>
  );
}
