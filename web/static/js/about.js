// about.js - About page: fill the live facts from /model-info once the API answers.
// Author: Colile Sibanda

document.addEventListener("DOMContentLoaded", () => {
  const banner = document.getElementById("page-banner");
  let loaded = false;

  /** Write one live fact into its <dd>. */
  function setFact(id, value) {
    document.getElementById(id).textContent = value;
  }

  async function load() {
    try {
      const info = await apiCall("/model-info");
      setFact("fact-model", `${info.model} (${info.architecture})`);
      setFact("fact-threshold",
        `${fmt(info.decision_threshold, 2)}, chosen by ${info.threshold_selection_metric} on the ${info.threshold_source} set`);
      setFact("fact-layers", info.layers.join(", "));
      clearChildren(banner);
      loaded = true;
    } catch (err) {
      showBanner(banner, err.message === "Failed to fetch"
        ? "Cannot reach the PhishGuard API, so the live facts are unavailable. The rest of this page does not need it."
        : err.message, "info");
    }
  }

  watchHealth(document.getElementById("pulse"), (ready) => {
    if (ready && !loaded) load();
  });
});
