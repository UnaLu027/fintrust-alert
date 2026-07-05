import { useHistory } from "../hooks/useHistory";
import { LoadingState } from "../components/common/LoadingState";
import { EmptyState } from "../components/common/EmptyState";
import { HistoryTable } from "../components/history/HistoryTable";

export function HistoryPage() {
  const { data, isLoading } = useHistory();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-brand-navy">分析紀錄</h1>
        <p className="mt-1 text-sm text-brand-muted">
          查看你過去查證過的資訊、模型輔助判斷結果與查證狀態。
        </p>
      </div>

      {isLoading ? (
        <LoadingState />
      ) : data && data.length > 0 ? (
        <HistoryTable items={data} />
      ) : (
        <EmptyState label="目前沒有分析紀錄" />
      )}
    </div>
  );
}
