import type { AnalysisType } from "../../types";
import { analysisTypeDescriptions, analysisTypeLabels } from "../../content/copy";

const options: AnalysisType[] = [
  "authenticity_check",
  "exaggeration_detection",
  "investment_inducement_risk",
  "multi_source_verification",
  "financial_statement_verification",
  "full_analysis",
];

interface Props {
  value: AnalysisType;
  onChange: (value: AnalysisType) => void;
}

export function AnalysisTypeSelector({ value, onChange }: Props) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {options.map((opt) => (
        <label
          key={opt}
          className={`cursor-pointer rounded-lg border p-3 text-sm transition-colors ${
            value === opt
              ? "border-brand-blue bg-brand-sky"
              : "border-brand-border hover:border-brand-blue/50"
          }`}
        >
          <div className="flex items-center gap-2">
            <input
              type="radio"
              name="analysisType"
              className="accent-brand-blue"
              checked={value === opt}
              onChange={() => onChange(opt)}
            />
            <span className="font-medium text-brand-navy">{analysisTypeLabels[opt]}</span>
          </div>
          <p className="mt-1 pl-6 text-xs leading-relaxed text-brand-muted">
            {analysisTypeDescriptions[opt]}
          </p>
        </label>
      ))}
    </div>
  );
}
