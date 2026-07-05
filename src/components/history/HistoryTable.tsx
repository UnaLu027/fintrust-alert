import { Link } from "react-router-dom";
import type { HistoryRecord } from "../../types";
import { RiskBadge } from "../common/RiskBadge";
import { VerificationStatusPill } from "../common/VerificationStatusPill";
import { SourceTag } from "../common/SourceTag";
import { analysisTypeLabels } from "../../content/copy";
import { useDeleteHistoryItem, useTrackHistoryItem } from "../../hooks/useHistory";

function formatTime(iso: string) {
  return new Date(iso).toLocaleString("zh-TW", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function HistoryTable({ items }: { items: HistoryRecord[] }) {
  const track = useTrackHistoryItem();
  const remove = useDeleteHistoryItem();

  return (
    <div className="overflow-x-auto rounded-xl border border-brand-border bg-white shadow-sm">
      <table className="min-w-full divide-y divide-brand-border text-sm">
        <thead className="bg-brand-surface text-left text-xs font-medium uppercase tracking-wide text-brand-muted">
          <tr>
            <th className="px-4 py-3">查詢內容</th>
            <th className="px-4 py-3">資料來源</th>
            <th className="px-4 py-3">分析類型</th>
            <th className="px-4 py-3">資訊分類</th>
            <th className="px-4 py-3">可信度風險</th>
            <th className="px-4 py-3">查證狀態</th>
            <th className="px-4 py-3">分析時間</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-brand-border">
          {items.map((item) => (
            <tr key={item.id} className="align-top hover:bg-brand-surface/60">
              <td className="max-w-xs px-4 py-3 font-medium text-brand-navy">
                {item.queryContent}
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1">
                  {item.dataSources.map((s) => (
                    <SourceTag key={s} source={s} />
                  ))}
                </div>
              </td>
              <td className="px-4 py-3 text-brand-muted">
                {analysisTypeLabels[item.analysisType]}
              </td>
              <td className="px-4 py-3">
                <VerificationStatusPill status={item.classification} />
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
                <div className="flex flex-wrap gap-2">
                  <Link
                    to={`/analysis/${item.analysisId}`}
                    className="whitespace-nowrap rounded-md border border-brand-blue px-2.5 py-1 text-xs font-medium text-brand-blue hover:bg-brand-sky"
                  >
                    查看結果
                  </Link>
                  <button
                    disabled={item.isTracked || track.isPending}
                    onClick={() => track.mutate(item.id)}
                    className="whitespace-nowrap rounded-md border border-brand-border px-2.5 py-1 text-xs font-medium text-brand-muted hover:border-brand-blue hover:text-brand-blue disabled:opacity-50"
                  >
                    {item.isTracked ? "已追蹤" : "加入追蹤"}
                  </button>
                  <button
                    disabled={remove.isPending}
                    onClick={() => remove.mutate(item.id)}
                    className="whitespace-nowrap rounded-md border border-risk-high/30 px-2.5 py-1 text-xs font-medium text-risk-high hover:bg-risk-high-bg disabled:opacity-50"
                  >
                    刪除紀錄
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
