import { Link } from "react-router-dom";
import type { PushAlert } from "../../types";
import { RiskBadge } from "../common/RiskBadge";
import { VerificationStatusPill } from "../common/VerificationStatusPill";
import { PushTemplatePreview } from "./PushTemplatePreview";
import { pushTemplateTypeLabels } from "../../content/copy";

function formatTime(iso: string) {
  return new Date(iso).toLocaleString("zh-TW", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function AlertRow({ alert }: { alert: PushAlert }) {
  return (
    <div className="rounded-xl border border-brand-border bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="inline-flex items-center rounded-full bg-brand-navy px-2.5 py-0.5 text-xs font-medium text-white">
          {pushTemplateTypeLabels[alert.templateType]}
        </span>
        <span className="text-xs text-brand-muted">{formatTime(alert.createdAt)}</span>
      </div>

      <h3 className="mt-2 font-medium text-brand-navy">{alert.title}</h3>

      <div className="mt-2 flex flex-wrap items-center gap-2">
        <span className="text-xs text-brand-muted">追蹤標的：{alert.relatedTarget}</span>
        <RiskBadge level={alert.riskLevel} />
        <VerificationStatusPill status={alert.verificationStatus} />
      </div>

      <p className="mt-2 text-sm text-brand-muted">推播原因：{alert.reason}</p>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        <PushTemplatePreview message={alert.message} />
        <Link
          to={`/analysis/${alert.analysisId}`}
          className="rounded-md border border-brand-blue px-3 py-1.5 text-xs font-medium text-brand-blue hover:bg-brand-sky"
        >
          查看查證結果
        </Link>
      </div>
    </div>
  );
}
