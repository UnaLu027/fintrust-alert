interface StatCardProps {
  label: string;
  value: number | string;
  unit?: string;
  tone?: "neutral" | "high" | "medium" | "low";
}

const toneStyles: Record<NonNullable<StatCardProps["tone"]>, string> = {
  neutral: "text-brand-navy",
  high: "text-risk-high",
  medium: "text-risk-medium",
  low: "text-risk-low",
};

export function StatCard({ label, value, unit = "則", tone = "neutral" }: StatCardProps) {
  return (
    <div className="rounded-xl border border-brand-border bg-white p-4 shadow-sm">
      <p className="text-sm text-brand-muted">{label}</p>
      <p className={`mt-2 text-3xl font-semibold ${toneStyles[tone]}`}>
        {value}
        <span className="ml-1 text-base font-normal text-brand-muted">{unit}</span>
      </p>
    </div>
  );
}
