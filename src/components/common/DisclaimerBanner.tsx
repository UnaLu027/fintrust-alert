interface DisclaimerBannerProps {
  text: string;
  tone?: "warning" | "muted";
}

export function DisclaimerBanner({ text, tone = "muted" }: DisclaimerBannerProps) {
  const toneStyles =
    tone === "warning"
      ? "border-risk-medium/30 bg-risk-medium-bg text-risk-medium"
      : "border-brand-border bg-brand-surface text-brand-muted";

  return (
    <div className={`rounded-lg border px-4 py-3 text-sm leading-relaxed ${toneStyles}`}>
      {text}
    </div>
  );
}
