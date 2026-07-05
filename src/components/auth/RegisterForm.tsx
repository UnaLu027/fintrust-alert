import { useState, type FormEvent } from "react";
import { useAuth } from "../../context/AuthContext";
import { TagInput } from "../common/TagInput";
import { ApiClientError } from "../../lib/apiClient";
import {
  alertFrequencyLabels,
  alertTypePrefLabels,
  investmentExperienceLabels,
  watchedMarketLabels,
} from "../../content/copy";
import type {
  AlertFrequency,
  AlertTypePref,
  InvestmentExperience,
  WatchedMarket,
} from "../../types";

const investmentExperienceOptions = Object.keys(
  investmentExperienceLabels,
) as InvestmentExperience[];
const watchedMarketOptions = Object.keys(watchedMarketLabels) as WatchedMarket[];
const alertFrequencyOptions = Object.keys(alertFrequencyLabels) as AlertFrequency[];
const alertTypeOptions = Object.keys(alertTypePrefLabels) as AlertTypePref[];

function toggleValue<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
}

export function RegisterForm({ onSuccess }: { onSuccess: () => void }) {
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [investmentExperience, setInvestmentExperience] =
    useState<InvestmentExperience>("beginner");
  const [watchedMarkets, setWatchedMarkets] = useState<WatchedMarket[]>(["tw_stock"]);
  const [watchedCompanies, setWatchedCompanies] = useState<string[]>(["台積電", "2330"]);
  const [watchedIndustries, setWatchedIndustries] = useState<string[]>(["AI"]);
  const [watchedKeywords, setWatchedKeywords] = useState<string[]>(["財報", "重大訊息"]);
  const [alertFrequency, setAlertFrequency] = useState<AlertFrequency>("high_risk_only");
  const [alertTypes, setAlertTypes] = useState<AlertTypePref[]>([
    "suspected_false",
    "pending_verification",
  ]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await register({
        email,
        password,
        investmentExperience,
        watchedMarkets,
        watchedCompanies,
        watchedIndustries,
        watchedKeywords,
        alertFrequency,
        alertTypes,
      });
      onSuccess();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "註冊失敗，請稍後再試");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-brand-navy">帳號資訊</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-brand-navy">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-md border border-brand-border px-3 py-2 text-sm outline-none focus:border-brand-blue"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-brand-navy">密碼</label>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-md border border-brand-border px-3 py-2 text-sm outline-none focus:border-brand-blue"
            />
          </div>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-brand-navy">投資經驗</h2>
        <div className="flex flex-wrap gap-3">
          {investmentExperienceOptions.map((opt) => (
            <label
              key={opt}
              className={`cursor-pointer rounded-md border px-3 py-2 text-sm ${
                investmentExperience === opt
                  ? "border-brand-blue bg-brand-sky text-brand-blue"
                  : "border-brand-border text-brand-muted"
              }`}
            >
              <input
                type="radio"
                name="investmentExperience"
                className="sr-only"
                checked={investmentExperience === opt}
                onChange={() => setInvestmentExperience(opt)}
              />
              {investmentExperienceLabels[opt]}
            </label>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-brand-navy">關注市場</h2>
        <div className="flex flex-wrap gap-3">
          {watchedMarketOptions.map((opt) => (
            <label
              key={opt}
              className={`cursor-pointer rounded-md border px-3 py-2 text-sm ${
                watchedMarkets.includes(opt)
                  ? "border-brand-blue bg-brand-sky text-brand-blue"
                  : "border-brand-border text-brand-muted"
              }`}
            >
              <input
                type="checkbox"
                className="sr-only"
                checked={watchedMarkets.includes(opt)}
                onChange={() => setWatchedMarkets(toggleValue(watchedMarkets, opt))}
              />
              {watchedMarketLabels[opt]}
            </label>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-brand-navy">追蹤公司或股票代號</h2>
        <TagInput
          values={watchedCompanies}
          onChange={setWatchedCompanies}
          placeholder="例如：台積電、2330、鴻海"
          suggestions={["台積電", "2330", "鴻海", "2317", "聯發科", "2454"]}
        />
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-brand-navy">追蹤產業</h2>
        <TagInput
          values={watchedIndustries}
          onChange={setWatchedIndustries}
          placeholder="例如：AI、半導體、電動車"
          suggestions={["AI", "半導體", "電動車"]}
        />
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-brand-navy">追蹤關鍵字</h2>
        <TagInput
          values={watchedKeywords}
          onChange={setWatchedKeywords}
          placeholder="例如：財報、重大訊息、暴跌"
          suggestions={["財報", "重大訊息", "暴跌", "爆料", "假新聞", "利多", "利空"]}
        />
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-brand-navy">提醒頻率</h2>
        <div className="flex flex-wrap gap-3">
          {alertFrequencyOptions.map((opt) => (
            <label
              key={opt}
              className={`cursor-pointer rounded-md border px-3 py-2 text-sm ${
                alertFrequency === opt
                  ? "border-brand-blue bg-brand-sky text-brand-blue"
                  : "border-brand-border text-brand-muted"
              }`}
            >
              <input
                type="radio"
                name="alertFrequency"
                className="sr-only"
                checked={alertFrequency === opt}
                onChange={() => setAlertFrequency(opt)}
              />
              {alertFrequencyLabels[opt]}
            </label>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-brand-navy">提醒類型</h2>
        <div className="flex flex-wrap gap-3">
          {alertTypeOptions.map((opt) => (
            <label
              key={opt}
              className={`cursor-pointer rounded-md border px-3 py-2 text-sm ${
                alertTypes.includes(opt)
                  ? "border-brand-blue bg-brand-sky text-brand-blue"
                  : "border-brand-border text-brand-muted"
              }`}
            >
              <input
                type="checkbox"
                className="sr-only"
                checked={alertTypes.includes(opt)}
                onChange={() => setAlertTypes(toggleValue(alertTypes, opt))}
              />
              {alertTypePrefLabels[opt]}
            </label>
          ))}
        </div>
      </section>

      {error && <p className="text-sm text-risk-high">{error}</p>}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full rounded-md bg-brand-blue py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-navy disabled:opacity-60"
      >
        {isSubmitting ? "註冊中..." : "完成註冊"}
      </button>
    </form>
  );
}
