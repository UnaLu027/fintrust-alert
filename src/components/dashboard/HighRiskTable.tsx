import { Link } from "react-router-dom";
import type { AnalysisResult } from "../../types";
import { RiskBadge } from "../common/RiskBadge";
import { VerificationStatusPill } from "../common/VerificationStatusPill";
import { SourceTag } from "../common/SourceTag";
import { modelJudgmentShortLabel } from "../../content/copy";

function formatTime(iso: string) {
  return new Date(iso).toLocaleString("zh-TW", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function HighRiskTable({ items }: { items: AnalysisResult[] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-brand-border bg-white shadow-sm">
      <table className="min-w-full divide-y divide-brand-border text-sm">
        <thead className="bg-brand-surface text-left text-xs font-medium uppercase tracking-wide text-brand-muted">
          <tr>
            <th className="px-4 py-3">標題</th>
            <th className="px-4 py-3">公司／關鍵字</th>
            <th className="px-4 py-3">資料來源</th>
            <th className="px-4 py-3">模型判斷</th>
            <th className="px-4 py-3">可信度風險</th>
            <th className="px-4 py-3">查證狀態</th>
            <th className="px-4 py-3">時間</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-brand-border">
          {items.map((item) => (
            <tr key={item.id} className="align-top hover:bg-brand-surface/60">
              <td className="max-w-xs px-4 py-3 font-medium text-brand-navy">{item.title}</td>
              <td className="px-4 py-3 text-brand-muted">
                {item.relatedCompany ?? item.relatedTicker ?? "-"}
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1">
                  {item.sources.map((s) => (
                    <SourceTag key={s} source={s} />
                  ))}
                </div>
              </td>
              <td className="px-4 py-3 text-brand-muted">
                {modelJudgmentShortLabel[item.verificationStatus]}
              </td>
              <td className="px-4 py-3">
                <RiskBadge level={item.riskLevel} />
              </td>
              <td className="px-4 py-3">
                <VerificationStatusPill status={item.verificationStatus} />
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-brand-muted">
                {formatTime(item.analyzedAt)}
              </td>
              <td className="px-4 py-3">
                <Link
                  to={`/analysis/${item.id}`}
                  className="whitespace-nowrap rounded-md border border-brand-blue px-3 py-1.5 text-xs font-medium text-brand-blue hover:bg-brand-sky"
                >
                  查看查證結果
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
