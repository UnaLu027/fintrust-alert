export function LoadingState({ label = "資料載入中..." }: { label?: string }) {
  return <div className="py-12 text-center text-sm text-brand-muted">{label}</div>;
}
