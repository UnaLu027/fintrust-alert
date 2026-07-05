import { useDashboardSummary, useHighRiskList } from "../hooks/useDashboard";
import { StatCard } from "../components/common/StatCard";
import { DisclaimerBanner } from "../components/common/DisclaimerBanner";
import { LoadingState } from "../components/common/LoadingState";
import { EmptyState } from "../components/common/EmptyState";
import { HighRiskTable } from "../components/dashboard/HighRiskTable";
import { dashboardCopy } from "../content/copy";
import { dashboardHighRiskBannerText } from "../content/disclaimers";

export function DashboardPage() {
  const summary = useDashboardSummary();
  const highRisk = useHighRiskList();

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-brand-navy">{dashboardCopy.title}</h1>
        <p className="mt-1 text-sm text-brand-muted">{dashboardCopy.subtitle}</p>
      </div>

      {summary.isLoading || !summary.data ? (
        <LoadingState />
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          <StatCard label="今日分析資訊" value={summary.data.todayAnalyzedCount} />
          <StatCard label="高風險提醒" value={summary.data.highRiskCount} tone="high" />
          <StatCard label="待查證資訊" value={summary.data.pendingVerificationCount} tone="medium" />
          <StatCard label="多來源不一致" value={summary.data.sourceInconsistentCount} tone="medium" />
          <StatCard label="官方已確認" value={summary.data.officialConfirmedCount} tone="low" />
        </div>
      )}

      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-brand-navy">今日高風險資訊</h2>
        <DisclaimerBanner text={dashboardHighRiskBannerText} tone="warning" />
        {highRisk.isLoading ? (
          <LoadingState />
        ) : highRisk.data && highRisk.data.length > 0 ? (
          <HighRiskTable items={highRisk.data} />
        ) : (
          <EmptyState label="今日尚無高風險資訊" />
        )}
      </div>
    </div>
  );
}
