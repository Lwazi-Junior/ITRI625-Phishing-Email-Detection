// model.js - Model page: fetch the saved test results from /metrics and
// show a verdict line and the CNN against baseline table.
// Author: Colile Sibanda

/** Write the verdict line from the final test metadata. */
function renderSummary(test) {
  const wrap = document.getElementById("summary");
  clearChildren(wrap);
  const line = document.createElement("p");
  line.className = "verdict positive";
  line.textContent =
    `On ${test.test_samples.toLocaleString()} unseen emails the CNN scored ` +
    `F1 ${fmt(test.final_f1, 4)}: it missed ${test.false_negatives} phishing emails ` +
    `and raised ${test.false_positives} false alarms, at the threshold of ` +
    `${fmt(test.classification_threshold, 2)} chosen on validation data.`;
  wrap.appendChild(line);
}

/** Build the metric comparison table. */
function renderComparison(rows) {
  const wrap = document.getElementById("comparison");
  clearChildren(wrap);
  const table = buildTable(rows.map((r) => ({
    metric: r.metric,
    "logistic regression": fmt(r.logistic_regression, 4),
    "1D CNN": fmt(r.cnn, 4),
  })));
  if (table) wrap.appendChild(table);
  wrap.appendChild(paragraph(
    "Higher is better for every row except Log Loss, False Positive Rate and False Negative Rate.", "hint"));
}

document.addEventListener("DOMContentLoaded", async () => {
  const banner = document.getElementById("page-banner");
  watchHealth(document.getElementById("pulse"));
  try {
    const body = await apiCall("/metrics");
    renderSummary(body.final_test);
    renderComparison(body.comparison);
  } catch (err) {
    showBanner(banner, err.message === "Failed to fetch"
      ? "Cannot reach the PhishGuard API. Start it with start_api.bat and reload this page."
      : err.message, "error");
  }
});
