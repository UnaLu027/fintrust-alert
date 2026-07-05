import { VerifyForm } from "../components/verify/VerifyForm";
import { verifyCopy } from "../content/copy";

export function QuickVerifyPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-brand-navy">{verifyCopy.title}</h1>
        <p className="mt-1 text-sm text-brand-muted">{verifyCopy.subtitle}</p>
      </div>
      <div className="rounded-xl border border-brand-border bg-white p-6 shadow-sm">
        <VerifyForm />
      </div>
    </div>
  );
}
