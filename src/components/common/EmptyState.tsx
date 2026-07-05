export function EmptyState({ label }: { label: string }) {
  return (
    <div className="rounded-lg border border-dashed border-brand-border py-12 text-center text-sm text-brand-muted">
      {label}
    </div>
  );
}
