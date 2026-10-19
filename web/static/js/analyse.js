// analyse.js - Analyse page: send the email to /predict for the verdict,
// then to /explain for the LIME word weights, and show both.
// Author: Colile Sibanda

const PHISHING_EXAMPLE =
  "URGENT: Your account has been locked. Verify your password immediately " +
  "by clicking this link or your mailbox will be closed within 24 hours.";

const LEGITIMATE_EXAMPLE =
  "Hi team, please remember that our project meeting is scheduled for " +
  "tomorrow at 10:00. The agenda is attached. Regards, Michael.";

// Five shades per direction: enough to read strength without implying a
// precision the weights do not have.
const SHADES = 5;

/** Format a probability as a percentage without rounding to 0% or 100%. */
function percent(p) {
  if (p < 0.001) return "under 0.1%";
  if (p > 0.999) return "over 99.9%";
  return `${(p * 100).toFixed(1)}%`;
}

/** Fill the verdict line, the probability meter and the details from /predict. */
function renderVerdict(result) {
  const verdict = document.getElementById("verdict");
  const meter = document.getElementById("meter");
  const details = document.getElementById("details");
  [verdict, meter, details].forEach(clearChildren);

  const phishing = result.predicted_class === 1;
  const line = document.createElement("p");
  line.className = phishing ? "verdict phishing" : "verdict positive";
  line.textContent =
    `${phishing ? "Likely phishing" : "Likely legitimate"}: the model gives this email ` +
    `${percent(result.phishing_probability)} probability of being phishing, ` +
    `${phishing ? "at or above" : "below"} the decision threshold of ${fmt(result.threshold, 2)}.`;
  verdict.appendChild(line);

  const bar = document.createElement("div");
  bar.className = "meter";
  bar.setAttribute("role", "img");
  bar.setAttribute("aria-label",
    `Probability ${fmt(result.phishing_probability, 3)}, threshold ${fmt(result.threshold, 2)}`);
  const fill = document.createElement("span");
  fill.className = "meter-fill";
  fill.style.width = `${result.phishing_probability * 100}%`;
  const mark = document.createElement("span");
  mark.className = "meter-mark";
  mark.style.left = `${result.threshold * 100}%`;
  bar.append(fill, mark);
  meter.append(bar, paragraph(
    `Bar: probability of phishing, from 0 at the left to 1 at the right. ` +
    `Black line: decision threshold (${fmt(result.threshold, 2)}), chosen on validation data.`, "hint"));

  const facts = [
    ["Risk level", result.risk_level],
    ["Confidence in this verdict", percent(result.confidence)],
    ["Model", result.model],
  ];
  for (const [term, value] of facts) {
    const dt = document.createElement("dt");
    dt.textContent = term;
    const dd = document.createElement("dd");
    dd.textContent = value;
    details.append(dt, dd);
  }
}

/** Pick the CSS classes for one weight relative to the strongest one. */
function shadeClass(weight, strongest) {
  if (weight === 0 || strongest === 0) return "";
  const step = Math.min(Math.floor((Math.abs(weight) / strongest) * SHADES), SHADES - 1) + 1;
  return `${weight > 0 ? "tok-p" : "tok-l"} s${step}`;
}

/**
 * Show the email with each LIME feature word underlined by its weight.
 * LIME splits the text on non-word characters, so the same split is used
 * here and every occurrence of a feature word is marked.
 * Inputs: container; text - the email as sent; features - [{feature, weight}].
 */
function renderWords(container, text, features) {
  clearChildren(container);
  const weights = new Map(features.map((f) => [f.feature, f.weight]));
  const strongest = features.reduce((m, f) => Math.max(m, Math.abs(f.weight)), 0);
  for (const part of text.split(/(\w+)/)) {
    const weight = weights.get(part);
    if (weight === undefined) {
      container.appendChild(document.createTextNode(part));
      continue;
    }
    const span = document.createElement("span");
    span.className = shadeClass(weight, strongest);
    span.textContent = part;
    span.title = `${part}: weight ${fmt(weight, 4)}, ${weight > 0 ? "towards phishing" : "towards legitimate"}`;
    container.appendChild(span);
  }
}

/** Fill the signals table and the method note from an /explain body. */
function renderExplanation(text, result) {
  renderWords(document.getElementById("tokens"), text, result.features);
  const signals = document.getElementById("signals");
  clearChildren(signals);
  const rows = result.features.map((f) => ({
    word: f.feature,
    direction: f.weight > 0 ? "towards phishing" : "towards legitimate",
    weight: fmt(f.weight, 4),
  }));
  const table = buildTable(rows);
  signals.appendChild(table || paragraph("No word carried any weight in this explanation.", "hint"));
  const method = document.getElementById("method");
  clearChildren(method);
  method.appendChild(explainer("How this explanation was made", [
    `Method: ${result.method}, ${result.num_samples} perturbed copies of the email, ` +
      `the ${result.num_features} most influential words kept.`,
    "A positive weight pushed the score towards phishing; a negative weight pushed it towards legitimate.",
    "LIME is a local approximation of this one prediction, not proof of what the model learned in general.",
  ]));
}

document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("email");
  const button = document.getElementById("analyse");
  const banner = document.getElementById("page-banner");
  const count = document.getElementById("count");
  const resultCard = document.getElementById("result-card");
  const whyCard = document.getElementById("why-card");

  const updateCount = () => {
    const text = input.value.trim();
    const words = text ? text.split(/\s+/).length : 0;
    count.textContent = `${words} words, ${text.length} characters`;
  };

  const reset = () => {
    resultCard.hidden = true;
    whyCard.hidden = true;
  };

  async function analyse() {
    const text = input.value.trim();
    if (!text) {
      showBanner(banner, "Enter some email text before clicking Analyse email.", "error");
      return;
    }
    button.disabled = true;
    button.textContent = "Analysing...";
    reset();
    const started = Date.now();
    const tick = () => showBanner(banner,
      `Explaining the verdict: ${Math.round((Date.now() - started) / 1000)} s. LIME scores ` +
      "1 000 variations of the email, which takes seconds locally and longer on the hosted demo.", "info");
    let timer = null;
    try {
      // The verdict is fast; show it first, then fill in the slower explanation.
      const body = { email_text: text };
      renderVerdict(await apiCall("/predict", { method: "POST", body }));
      resultCard.hidden = false;
      tick();
      timer = setInterval(tick, 1000);
      const result = await apiCall("/explain", { method: "POST", body: { ...body, num_features: 10 } });
      clearInterval(timer);
      clearChildren(banner);
      renderExplanation(text, result);
      whyCard.hidden = false;
    } catch (err) {
      clearInterval(timer);
      showBanner(banner, err.message === "Failed to fetch"
        ? "Cannot reach the PhishGuard API. Start it with start_api.bat and reload this page."
        : err.message, "error");
    } finally {
      button.disabled = false;
      button.textContent = "Analyse email";
    }
  }

  input.addEventListener("input", updateCount);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) analyse();
  });
  button.addEventListener("click", analyse);
  for (const [id, sample] of [["example-phish", PHISHING_EXAMPLE], ["example-legit", LEGITIMATE_EXAMPLE]]) {
    document.getElementById(id).addEventListener("click", () => {
      input.value = sample;
      updateCount();
      reset();
    });
  }
  document.getElementById("clear").addEventListener("click", () => {
    input.value = "";
    updateCount();
    clearChildren(banner);
    reset();
    input.focus();
  });
  watchHealth(document.getElementById("pulse"));
});
