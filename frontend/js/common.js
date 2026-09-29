/* =====================================================================
   Shared helpers: API calls, safe DOM building, session storage, charts.

   XSS PROTECTION: every piece of text is inserted with textContent via
   el(). We never build HTML strings from data, so nothing coming from the
   API can be interpreted as markup or script.
   ===================================================================== */

const App = (() => {
  const STORAGE_KEYS = {
    responses: "smpra.responses",
    result: "smpra.result",
    simulation: "smpra.simulation",
  };

  const LEVEL_LABELS = { LOW: "Low", MODERATE: "Moderate", HIGH: "High", CRITICAL: "Critical" };
  const PRIORITY_LABELS = { IMMEDIATE: "Immediate", IMPORTANT: "Important", GOOD_PRACTICE: "Good practice" };

  /* ---------------------------------------------------------------- DOM */
  function el(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs || {})) {
      if (value === null || value === undefined || value === false) continue;
      if (key === "class") node.className = value;
      else if (key === "text") node.textContent = value;
      else if (key === "dataset") Object.assign(node.dataset, value);
      else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2), value);
      else node.setAttribute(key, value === true ? "" : value);
    }
    for (const child of children.flat()) {
      if (child === null || child === undefined || child === false) continue;
      node.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }
    return node;
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
    return node;
  }

  function levelBadge(level) {
    return el("span", { class: `level level-${level}` }, `${(LEVEL_LABELS[level] || level).toUpperCase()} RISK`);
  }

  /* ---------------------------------------------------------------- API */
  async function api(path, options = {}) {
    const init = { method: options.method || "GET", headers: { Accept: "application/json" } };
    if (options.body !== undefined) {
      init.headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(options.body);
    }
    if (options.headers) Object.assign(init.headers, options.headers);

    let response;
    try {
      response = await fetch(path, init);
    } catch (err) {
      throw new Error("Can't reach the assessment server. Check that `python run.py` is still running.");
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = Array.isArray(data.details) ? ` ${data.details.join(" ")}` : "";
      throw new Error(`${data.error || `Request failed (${response.status}).`}${detail}`);
    }
    return data;
  }

  /* ---------------------------------------------------------------- storage
     sessionStorage lives only in this browser tab and is cleared when the tab
     closes. Answers are never sent anywhere except to this local server for
     scoring, and the server does not store them. */
  function load(key) {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEYS[key]);
      return raw ? JSON.parse(raw) : null;
    } catch (err) {
      return null;
    }
  }
  function save(key, value) {
    try {
      sessionStorage.setItem(STORAGE_KEYS[key], JSON.stringify(value));
    } catch (err) {
      /* storage unavailable (private mode) - the page still works without it */
    }
  }
  function forget(...keys) {
    try {
      (keys.length ? keys : Object.keys(STORAGE_KEYS)).forEach((k) => sessionStorage.removeItem(STORAGE_KEYS[k]));
    } catch (err) { /* ignore */ }
  }

  /* ---------------------------------------------------------------- reports */
  function openReport(responses, download = false) {
    // A normal form POST opens the server-rendered report in a new tab.
    const form = el("form", { method: "POST", action: "/api/report", target: "_blank", class: "sr-only" },
      el("input", { type: "hidden", name: "responses_json", value: JSON.stringify(responses) }),
      download ? el("input", { type: "hidden", name: "download", value: "1" }) : null);
    document.body.append(form);
    form.submit();
    form.remove();
  }

  /* ---------------------------------------------------------------- charts */
  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }
  function levelOf(score) {
    if (score <= 20) return "LOW";
    if (score <= 40) return "MODERATE";
    if (score <= 70) return "HIGH";
    return "CRITICAL";
  }
  function levelColor(level) {
    return cssVar({ LOW: "--good", MODERATE: "--warning", HIGH: "--serious", CRITICAL: "--critical" }[level]);
  }

  const charts = {};

  /**
   * Draw a bar chart. Always also renders a data table (inside <details>) so the
   * numbers are available without colour and when the CDN is blocked.
   *   opts: { labels, datasets:[{label, data, colors?|color?}], horizontal, max, suffix, legend }
   */
  function barChart(canvasId, opts) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    renderTable(canvas, opts);

    if (typeof window.Chart === "undefined") {
      const box = canvas.closest(".chart-box");
      if (box) box.replaceChildren(el("p", { class: "notice" }, "Charts need the Chart.js library, which could not load (offline?). The table below has the same data."));
      return;
    }

    if (charts[canvasId]) charts[canvasId].destroy();
    const ink2 = cssVar("--ink-2");
    const grid = cssVar("--grid");
    const surface = cssVar("--surface");
    const suffix = opts.suffix || "";

    charts[canvasId] = new window.Chart(canvas, {
      type: "bar",
      data: {
        labels: opts.labels,
        datasets: opts.datasets.map((d) => ({
          label: d.label,
          data: d.data,
          backgroundColor: d.colors || d.color || cssVar("--series-1"),
          borderColor: surface,
          borderWidth: { top: 0, bottom: 0, left: 0, right: 0 },
          borderRadius: 4,
          borderSkipped: "start",
          maxBarThickness: 20,
          categoryPercentage: opts.datasets.length > 1 ? 0.7 : 0.8,
          barPercentage: opts.datasets.length > 1 ? 0.92 : 0.9,
        })),
      },
      options: {
        indexAxis: opts.horizontal ? "y" : "x",
        responsive: true,
        maintainAspectRatio: false,
        animation: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? false : { duration: 500 },
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: {
            display: opts.legend !== undefined ? opts.legend : opts.datasets.length > 1,
            position: "top",
            align: "start",
            labels: { color: ink2, boxWidth: 10, boxHeight: 10, usePointStyle: false, font: { family: cssVar("--font-body") } },
          },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const value = ctx.parsed[opts.horizontal ? "x" : "y"];
                const level = opts.showLevel ? ` (${LEVEL_LABELS[levelOf(value)]})` : "";
                return ` ${ctx.dataset.label}: ${value}${suffix}${level}`;
              },
            },
          },
        },
        scales: {
          [opts.horizontal ? "x" : "y"]: {
            beginAtZero: true,
            max: opts.max,
            grid: { color: grid, drawTicks: false },
            border: { display: false },
            ticks: { color: cssVar("--muted"), padding: 6, callback: (v) => `${v}${suffix}` },
          },
          [opts.horizontal ? "y" : "x"]: {
            grid: { display: false },
            border: { color: cssVar("--axis") },
            ticks: { color: ink2, autoSkip: false, font: { size: 12 } },
          },
        },
      },
    });
  }

  function renderTable(canvas, opts) {
    const holder = canvas.closest(".chart-wrap")?.querySelector(".chart-fallback");
    if (!holder) return;
    const suffix = opts.suffix || "";
    const table = el("table", { class: "data" },
      el("thead", {}, el("tr", {}, el("th", {}, opts.tableHeading || "Item"),
        opts.datasets.map((d) => el("th", { class: "num" }, d.label)))),
      el("tbody", {}, opts.labels.map((label, i) =>
        el("tr", {}, el("td", {}, label), opts.datasets.map((d) => el("td", { class: "num" }, `${d.data[i]}${suffix}`))))));
    clear(holder).append(el("summary", {}, "Show data as a table"), table);
  }

  function markCurrentNav() {
    const here = location.pathname.replace(/\/$/, "/index.html");
    document.querySelectorAll(".nav a").forEach((a) => {
      if (here.endsWith(a.getAttribute("href"))) a.setAttribute("aria-current", "page");
    });
  }
  document.addEventListener("DOMContentLoaded", markCurrentNav);

  return { el, clear, api, load, save, forget, openReport, levelBadge, barChart, levelOf, levelColor, cssVar, LEVEL_LABELS, PRIORITY_LABELS };
})();
