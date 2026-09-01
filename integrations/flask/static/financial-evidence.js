(() => {
  const formatValue = (metric) => {
    const value = metric.latest_value ?? metric.value ?? null;
    if (value === null || value === undefined) return "—";
    const unit = metric.unit ? ` ${metric.unit}` : "";
    if (typeof value === "number") {
      return `${Number(value.toFixed ? value.toFixed(4) : value).toLocaleString()}${unit}`;
    }
    return `${value}${unit}`;
  };

  const metricCard = (metric) => {
    const change = metric.change_percent;
    const changeText = typeof change === "number" ? `${change.toFixed(2)}%` : "—";
    return `
      <article class="financial-metric">
        <h3>${metric.label || metric.code}</h3>
        <p class="financial-metric__value">${formatValue(metric)}</p>
        <p class="financial-metric__change">變化幅度：${changeText}</p>
        ${metric.formula ? `<p class="financial-metric__formula">公式：${metric.formula}</p>` : ""}
      </article>
    `;
  };

  const renderSnapshot = (root, snapshot) => {
    const status = root.querySelector("[data-fintrust-status]");
    const summary = root.querySelector("[data-fintrust-summary]");
    const metrics = root.querySelector("[data-fintrust-metrics]");
    const limitations = root.querySelector("[data-fintrust-limitations]");

    status.textContent = `${snapshot.company_name || snapshot.ticker}｜${snapshot.subindustry || "半導體"}｜整體狀態：${snapshot.overall_severity || "unknown"}`;
    summary.hidden = false;
    summary.textContent = snapshot.summary || "目前尚無摘要。";

    const keyMetrics = snapshot.key_metrics || [];
    metrics.hidden = keyMetrics.length === 0;
    metrics.innerHTML = keyMetrics.slice(0, 6).map(metricCard).join("");

    const items = snapshot.limitations || [];
    limitations.hidden = items.length === 0;
    const list = limitations.querySelector("ul");
    if (list) {
      list.innerHTML = items.map((item) => `<li>${item}</li>`).join("");
    }
  };

  const loadEvidence = async (root) => {
    const input = root.querySelector("#fintrust-ticker");
    const ticker = (input?.value || root.dataset.ticker || "2330").trim();
    const status = root.querySelector("[data-fintrust-status]");
    status.textContent = "正在載入官方財報證據…";
    try {
      const response = await fetch(`/api/financial/companies/${encodeURIComponent(ticker)}/analysis/latest`);
      const payload = await response.json();
      if (!response.ok || payload.success === false) {
        throw new Error(payload.error || "財報證據暫時無法取得。");
      }
      renderSnapshot(root, payload.data || payload);
    } catch (error) {
      status.textContent = error.message || "財報證據暫時無法取得。";
    }
  };

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-financial-evidence]").forEach((root) => {
      root.querySelector("[data-fintrust-load]")?.addEventListener("click", () => loadEvidence(root));
      loadEvidence(root);
    });
  });
})();
