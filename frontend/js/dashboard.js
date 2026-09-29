/* Dashboard: latest assessment (this tab only) + synthetic aggregate charts. */
(() => {
  const { el, clear, api, load, levelBadge, barChart, levelColor, cssVar, LEVEL_LABELS } = App;
  const $ = (id) => document.getElementById(id);

  function stat(label, value, suffix) {
    return el("div", { class: "stat" },
      el("div", { class: "label" }, label),
      el("div", { class: "value" }, value instanceof Node ? value : String(value), suffix ? el("small", {}, suffix) : null));
  }

  function renderSummary(result) {
    const holder = $("my-summary");
    if (!result) {
      holder.append(el("div", { class: "card empty" },
        el("h2", {}, "No assessment in this tab yet"),
        el("p", {}, "Complete the questionnaire to see your own scores next to the synthetic population."),
        el("a", { class: "btn btn-primary", href: "assessment.html" }, "Start privacy assessment")));
      return;
    }
    holder.append(el("div", { class: "stats" },
      stat("Overall risk score", result.overall_score, "/100"),
      stat("Risk level", levelBadge(result.risk_level)),
      stat("High-risk categories", result.high_risk_categories.length, " of 10"),
      stat("Recommendations", result.recommendations.length),
      stat("Security controls on", result.security_controls.enabled_count, ` of ${result.security_controls.total}`)));
  }

  function renderImprovement(sim, labels) {
    const body = $("improvement-body");
    if (!sim) {
      body.append(el("div", { class: "empty" },
        el("p", {}, "Run the improvement simulator on your results to compare your current and simulated scores here."),
        el("a", { class: "btn btn-secondary", href: "assessment.html#results" }, "Open my results")));
      return;
    }
    body.append(el("p", {},
      "Overall ", el("strong", {}, `${sim.current.overall_score} → ${sim.simulated.overall_score}`),
      ` (${LEVEL_LABELS[sim.current.risk_level]} → ${LEVEL_LABELS[sim.simulated.risk_level]}), a reduction of `,
      el("span", { class: "marker" }, `${sim.risk_reduction} points`), ". This is a framework simulation, not a guarantee."));
    $("improvement-box").hidden = false;
    const keys = Object.keys(sim.category_changes);
    barChart("chart-improvement", {
      labels: keys.map((k) => labels[k]),
      datasets: [
        { label: "Current", data: keys.map((k) => sim.category_changes[k].before), color: cssVar("--series-2") },
        { label: "Simulated", data: keys.map((k) => sim.category_changes[k].after), color: cssVar("--series-1") },
      ],
      horizontal: true, max: 100, tableHeading: "Category",
    });
  }

  async function init() {
    const result = load("result");
    renderSummary(result);

    let stats;
    try {
      stats = await api("/api/dashboard/stats");
    } catch (err) {
      $("dash").replaceWith(el("p", { class: "notice error" }, err.message));
      return;
    }
    const labels = stats.category_labels;
    const syn = stats.synthetic;
    const keys = Object.keys(labels);

    renderImprovement(load("simulation"), labels);

    if (!syn) {
      $("dash-source").textContent = "Synthetic dataset not found";
      $("dist-note").textContent = "Run `python data/generate_dataset.py` to create the synthetic dataset.";
      return;
    }
    $("dash-source").textContent = `${syn.total_records.toLocaleString()} synthetic records · average score ${syn.average_score}`;

    // 1. Category scores: you vs synthetic average
    const catSets = [{ label: "Synthetic average", data: keys.map((k) => syn.category_averages[k]), color: cssVar("--series-2") }];
    if (result) catSets.unshift({ label: "Your assessment", data: keys.map((k) => result.category_scores[k]), color: cssVar("--series-1") });
    barChart("chart-categories", {
      labels: keys.map((k) => labels[k]), datasets: catSets, horizontal: true, max: 100, legend: true, tableHeading: "Category",
    });

    // 2. Risk distribution (status colours + labels on the axis)
    const levels = ["LOW", "MODERATE", "HIGH", "CRITICAL"];
    $("dist-note").textContent = result
      ? `Your result: ${result.overall_score}/100 (${LEVEL_LABELS[result.risk_level]}). Bars show synthetic records per level.`
      : "Synthetic records per risk level.";
    barChart("chart-distribution", {
      labels: levels.map((l) => LEVEL_LABELS[l]),
      datasets: [{ label: "Records", data: levels.map((l) => syn.risk_distribution[l]), colors: levels.map(levelColor) }],
      legend: false, tableHeading: "Risk level",
    });

    // 3. Security controls adoption
    barChart("chart-controls", {
      labels: syn.control_adoption.map((c) => c.label),
      datasets: [{ label: "Turned on", data: syn.control_adoption.map((c) => c.percent_enabled) }],
      horizontal: true, max: 100, suffix: "%", legend: false, tableHeading: "Control",
    });

    // 4. Top weaknesses
    barChart("chart-weaknesses", {
      labels: syn.top_weaknesses.map((w) => w.label),
      datasets: [{ label: "Records", data: syn.top_weaknesses.map((w) => w.percent) }],
      horizontal: true, max: 100, suffix: "%", legend: false, tableHeading: "Weakness",
    });

    // 5. Digital footprint histogram
    barChart("chart-footprint", {
      labels: syn.digital_footprint_histogram.labels,
      datasets: [{ label: "Records", data: syn.digital_footprint_histogram.counts }],
      legend: false, tableHeading: "Score range",
    });

    const stored = stats.stored_assessments;
    $("stored-note").textContent = stored.total
      ? `${stored.total} anonymous result${stored.total === 1 ? " has" : "s have"} been saved on this server (average score ${stored.average_score}).`
      : "No results have been saved on this server. Saving is optional and off by default.";
  }

  init();
})();
