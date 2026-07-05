import { useAlerts } from "../hooks/useAlerts";
import { LoadingState } from "../components/common/LoadingState";
import { EmptyState } from "../components/common/EmptyState";
import { AlertRow } from "../components/alerts/AlertRow";

export function AlertsCenterPage() {
  const { data, isLoading } = useAlerts();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-brand-navy">追蹤與推播提醒中心</h1>
        <p className="mt-1 text-sm text-brand-muted">
          只有跟你追蹤的標的相關，且出現可信度風險、待查證、多來源不一致或官方查證更新時，系統才會推播提醒。
        </p>
      </div>

      {isLoading ? (
        <LoadingState />
      ) : data && data.length > 0 ? (
        <div className="space-y-4">
          {data.map((alert) => (
            <AlertRow key={alert.id} alert={alert} />
          ))}
        </div>
      ) : (
        <EmptyState label="目前沒有與你追蹤標的相關的推播提醒" />
      )}
    </div>
  );
}
