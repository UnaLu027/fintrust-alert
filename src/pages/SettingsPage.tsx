import { useEffect, useState } from "react";
import { useUpdateWatchlist, useWatchlist } from "../hooks/useWatchlist";
import { TagInput } from "../components/common/TagInput";
import { LoadingState } from "../components/common/LoadingState";
import {
  alertFrequencyLabels,
  alertTypePrefLabels,
} from "../content/copy";
import type { AlertFrequency, AlertTypePref } from "../types";

const alertFrequencyOptions = Object.keys(alertFrequencyLabels) as AlertFrequency[];
const alertTypeOptions = Object.keys(alertTypePrefLabels) as AlertTypePref[];

function toggleValue<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
}

export function SettingsPage() {
  const { data, isLoading } = useWatchlist();
  const updateWatchlist = useUpdateWatchlist();

  const [companies, setCompanies] = useState<string[]>([]);
  const [industries, setIndustries] = useState<string[]>([]);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [alertFrequency, setAlertFrequency] = useState<AlertFrequency>("high_risk_only");
  const [alertTypes, setAlertTypes] = useState<AlertTypePref[]>([]);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!data) return;
    setCompanies(data.items.filter((i) => i.type === "company").map((i) => i.value));
    setIndustries(data.items.filter((i) => i.type === "industry").map((i) => i.value));
    setKeywords(data.items.filter((i) => i.type === "keyword").map((i) => i.value));
    setAlertFrequency(data.alertFrequency);
    setAlertTypes(data.alertTypes);
  }, [data]);

  async function handleSave() {
    setSavedMessage(null);
    await updateWatchlist.mutateAsync({
      watchedCompanies: companies,
      watchedIndustries: industries,
      watchedKeywords: keywords,
      alertFrequency,
      alertTypes,
    });
    setSavedMessage("追蹤設定已更新");
  }

  if (isLoading) return <LoadingState />;

  return (
    <div className="max-w-2xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-brand-navy">會員設定</h1>
        <p className="mt-1 text-sm text-brand-muted">調整追蹤標的與提醒偏好。</p>
      </div>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-brand-navy">追蹤公司或股票代號</h2>
        <TagInput values={companies} onChange={setCompanies} placeholder="輸入後按 Enter 新增" />
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-brand-navy">追蹤產業</h2>
        <TagInput values={industries} onChange={setIndustries} placeholder="輸入後按 Enter 新增" />
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-brand-navy">追蹤關鍵字</h2>
        <TagInput values={keywords} onChange={setKeywords} placeholder="輸入後按 Enter 新增" />
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

      {savedMessage && <p className="text-sm text-risk-low">{savedMessage}</p>}

      <button
        onClick={handleSave}
        disabled={updateWatchlist.isPending}
        className="rounded-md bg-brand-blue px-6 py-2.5 text-sm font-semibold text-white hover:bg-brand-navy disabled:opacity-60"
      >
        {updateWatchlist.isPending ? "儲存中..." : "儲存設定"}
      </button>
    </div>
  );
}
