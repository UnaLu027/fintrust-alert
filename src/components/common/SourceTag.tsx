import type { SourceType } from "../../types";
import { sourceLabels } from "../../content/copy";

const styles: Record<SourceType, string> = {
  x: "bg-slate-900 text-white",
  yahoo: "bg-violet-600 text-white",
  mops: "bg-brand-navy text-white",
};

export function SourceTag({ source }: { source: SourceType }) {
  return (
    <span
      className={`inline-flex items-center rounded px-2 py-0.5 text-[11px] font-semibold tracking-wide ${styles[source]}`}
    >
      {sourceLabels[source]}
    </span>
  );
}
