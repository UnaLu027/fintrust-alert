import { DisclaimerBanner } from "../components/common/DisclaimerBanner";
import {
  analysisPipelineSteps,
  dataSourceText,
  fixedDisclaimer,
  systemPurposeText,
} from "../content/disclaimers";

export function AboutDisclaimerPage() {
  return (
    <div className="max-w-3xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-brand-navy">系統說明／免責說明</h1>
      </div>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold text-brand-navy">系統目的</h2>
        <p className="text-sm leading-relaxed text-brand-muted">{systemPurposeText}</p>
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold text-brand-navy">資料來源</h2>
        <p className="text-sm leading-relaxed text-brand-muted">{dataSourceText}</p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-brand-navy">分析流程</h2>
        <ol className="flex flex-wrap items-center gap-2 text-sm">
          {analysisPipelineSteps.map((step, i) => (
            <li key={step} className="flex items-center gap-2">
              <span className="rounded-full bg-brand-sky px-3 py-1 font-medium text-brand-blue">
                {step}
              </span>
              {i < analysisPipelineSteps.length - 1 && (
                <span className="text-brand-muted">→</span>
              )}
            </li>
          ))}
        </ol>
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold text-brand-navy">免責聲明</h2>
        <DisclaimerBanner text={fixedDisclaimer} />
      </section>
    </div>
  );
}
