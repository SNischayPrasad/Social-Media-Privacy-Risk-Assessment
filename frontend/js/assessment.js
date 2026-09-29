/* =====================================================================
   Assessment page: questionnaire -> results -> simulator -> report.

   Answers live only in this tab's sessionStorage and in memory. They are
   sent to the local server for scoring, and the server does not store them.
   ===================================================================== */
(() => {
  const { el, clear, api, load, save, forget, levelBadge, barChart, levelColor, levelOf, PRIORITY_LABELS } = App;

  const state = {
    categories: [],
    labels: {},        // category key -> short label (for charts)
    responses: load("responses") || {},
    current: 0,
    result: null,
  };

  const $ = (id) => document.getElementById(id);

  const MEANING = {
    LOW: "Limited exposure based on your answers. Keep reviewing your settings every few months.",
    MODERATE: "Some information or habits increase your exposure. A few targeted changes would reduce it noticeably.",
    HIGH: "Several categories expose significant information or lack key protections. Start with the Immediate recommendations.",
    CRITICAL: "Broad exposure combined with missing account protections. Work through the Immediate recommendations first.",
  };

  /* -------------------------------------------------------------- questionnaire */
  function totalQuestions() {
    return state.categories.reduce((n, c) => n + c.questions.length, 0);
  }

  function answeredIn(category) {
    return category.questions.filter((q) => state.responses[q.id]).length;
  }

  function renderSteps() {
    const list = clear($("steps"));
    state.categories.forEach((cat, index) => {
      const done = answeredIn(cat);
      const complete = done === cat.questions.length;
      list.append(el("li", {},
        el("button", {
          type: "button",
          "aria-current": index === state.current ? "step" : null,
          onclick: () => goTo(index),
        },
        el("span", { class: "code" }, cat.code),
        el("span", {}, cat.name),
        el("span", { class: `count${complete ? " done" : ""}` }, complete ? "Done" : `${done}/${cat.questions.length}`))));
    });

    const answered = Object.keys(state.responses).length;
    $("answered-count").textContent = answered;
    $("total-count").textContent = totalQuestions();
    $("progress-bar").style.width = `${(100 * answered) / totalQuestions()}%`;
  }

  function renderCategory() {
    const cat = state.categories[state.current];
    const last = state.current === state.categories.length - 1;
    $("cat-eyebrow").textContent = `Category ${cat.code} · ${state.current + 1} of ${state.categories.length}`;
    $("cat-title").textContent = cat.name;
    $("cat-desc").textContent = cat.description;

    const holder = clear($("questions"));
    cat.questions.forEach((q, i) => {
      const name = `q-${q.id}`;
      holder.append(el("div", { class: "card question", id: `card-${q.id}` },
        el("fieldset", {},
          el("legend", {}, `${cat.code}${i + 1}. ${q.text}`),
          el("p", { class: "help" }, q.help),
          el("div", { class: "options" }, q.options.map((opt) =>
            el("label", {},
              el("input", {
                type: "radio", name, value: opt.value,
                checked: state.responses[q.id] === opt.value,
                onchange: () => answer(q.id, opt.value),
              }),
              el("span", {}, opt.label)))))));
    });

    $("prev-btn").disabled = state.current === 0;
    $("next-btn").hidden = last;
    $("submit-btn").hidden = !last;
    $("submit-area").hidden = !last;
    $("form-error").hidden = true;
    renderSteps();
  }

  function answer(id, value) {
    state.responses[id] = value;
    save("responses", state.responses);
    $(`card-${id}`)?.classList.remove("missing");
    renderSteps();
  }

  function goTo(index) {
    state.current = Math.max(0, Math.min(index, state.categories.length - 1));
    renderCategory();
    $("cat-title").scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function showError(message) {
    const box = $("form-error");
    box.textContent = message;
    box.hidden = false;
  }

  async function submit() {
    // Client-side check first (the server validates again - never trust the client).
    const firstMissing = state.categories.findIndex((c) => answeredIn(c) < c.questions.length);
    if (firstMissing !== -1) {
      goTo(firstMissing);
      state.categories[firstMissing].questions
        .filter((q) => !state.responses[q.id])
        .forEach((q) => $(`card-${q.id}`)?.classList.add("missing"));
      const left = totalQuestions() - Object.keys(state.responses).length;
      showError(`${left} question${left === 1 ? " is" : "s are"} still unanswered. They're outlined in red in this category.`);
      return;
    }

    const button = $("submit-btn");
    button.disabled = true;
    button.textContent = "Calculating…";
    try {
      const result = await api("/api/assessment", {
        method: "POST",
        body: { responses: state.responses, store: $("store-consent").checked },
      });
      save("result", result);
      forget("simulation");
      history.replaceState(null, "", "#results");
      showResults(result);
    } catch (err) {
      showError(err.message);
    } finally {
      button.disabled = false;
      button.textContent = "Calculate my privacy score";
    }
  }

  /* -------------------------------------------------------------- results */
  function stat(label, value, suffix) {
    return el("div", { class: "stat" },
      el("div", { class: "label" }, label),
      el("div", { class: "value" }, String(value), suffix ? el("small", {}, suffix) : null));
  }

  function findingItem(f, rank) {
    return el("li", {},
      el("span", { class: "rank" }, String(rank).padStart(2, "0")),
      el("div", {},
        el("div", { class: "title" }, f.title),
        el("div", { class: "meta" }, el("span", { class: `sev sev-${f.severity}` }, f.severity), f.category_name)));
  }

  function showResults(result) {
    state.result = result;
    $("form-view").hidden = true;
    $("results").hidden = false;
    window.scrollTo({ top: 0 });

    const date = new Date(result.created_at).toLocaleString();
    $("result-meta").textContent = `Assessment ${result.assessment_id.slice(0, 8)} · ${date}`;
    clear($("score-number")).append(String(result.overall_score), el("small", {}, "/100"));
    clear($("score-level")).append(levelBadge(result.risk_level));
    $("score-meaning").textContent = MEANING[result.risk_level];
    $("scale-pointer").style.left = `${result.overall_score}%`;
    $("result-disclaimer").textContent = result.disclaimer;

    const immediate = result.recommendations.filter((r) => r.priority === "IMMEDIATE").length;
    clear($("stats")).append(
      stat("Findings", result.findings.length),
      stat("High-risk categories", result.high_risk_categories.length, " of 10"),
      stat("Immediate actions", immediate),
      stat("Recommendations", result.recommendations.length),
      stat("Security controls on", result.security_controls.enabled_count, ` of ${result.security_controls.total}`));

    // Category chart - bars coloured by risk level (legend + table give the same information).
    const keys = Object.keys(result.category_scores);
    barChart("category-chart", {
      labels: keys.map((k) => state.labels[k] || k),
      datasets: [{
        label: "Risk score",
        data: keys.map((k) => result.category_scores[k]),
        colors: keys.map((k) => levelColor(levelOf(result.category_scores[k]))),
      }],
      horizontal: true, max: 100, legend: false, showLevel: true, tableHeading: "Category",
    });

    // Findings
    $("finding-total").textContent = `${result.findings.length} total`;
    const top = clear($("top-findings"));
    if (!result.findings.length) top.append(el("li", {}, el("span", {}), el("div", {}, "No significant findings. Keep reviewing your settings periodically.")));
    result.top_findings.forEach((f, i) => top.append(findingItem(f, i + 1)));
    const all = clear($("all-findings"));
    result.findings.forEach((f, i) => all.append(findingItem(f, i + 1)));
    $("all-findings-wrap").hidden = result.findings.length <= 5;

    // Controls
    $("controls-total").textContent = `${result.security_controls.enabled_count} of ${result.security_controls.total} on`;
    clear($("controls-table")).append(
      el("thead", {}, el("tr", {}, el("th", {}, "Control"), el("th", {}, "Status"))),
      el("tbody", {}, result.security_controls.controls.map((c) =>
        el("tr", {}, el("td", {}, c.label), el("td", {}, c.enabled ? "✓ On" : el("span", { class: "marker" }, "✗ Off / unsure"))))));

    // Recommendations grouped by priority
    const recs = clear($("recommendations"));
    ["IMMEDIATE", "IMPORTANT", "GOOD_PRACTICE"].forEach((priority) => {
      const group = result.recommendations.filter((r) => r.priority === priority);
      if (!group.length) return;
      recs.append(el("div", { class: "rec-group" },
        el("h3", {}, PRIORITY_LABELS[priority], el("span", { class: "count" }, `${group.length}`)),
        group.map((r) => el("div", { class: "rec" },
          el("div", { class: "risk" }, `Risk: ${r.risk}`),
          el("div", { class: "text" }, r.recommendation),
          el("div", { class: "why" }, `Why it matters: ${r.why}`)))));
    });
    if (!result.recommendations.length) recs.append(el("p", {}, "No recommendations. Your answers show low exposure."));

    renderSimulatorOptions(result);
    const previous = load("simulation");
    if (previous) renderSimulation(previous);

    // Stored-result box (deletion token is shown once)
    const box = $("stored-box");
    clear(box);
    box.hidden = !result.stored;
    if (result.stored) {
      box.append(
        el("p", {}, el("strong", {}, "Saved anonymously. "), "Assessment ID: ", el("code", {}, result.assessment_id)),
        result.delete_token ? el("p", {}, "Deletion key (shown once, so copy it if you want to delete later): ", el("code", {}, result.delete_token)) : null,
        el("div", { class: "btn-row" },
          el("a", { class: "btn btn-secondary", href: `/api/assessment/${result.assessment_id}/report`, target: "_blank", rel: "noopener" }, "Open saved report"),
          result.delete_token ? el("button", { class: "btn btn-ghost", type: "button", onclick: deleteStored }, "Delete my saved result") : null));
    }
  }

  async function deleteStored() {
    const result = state.result;
    try {
      await api(`/api/assessment/${result.assessment_id}`, { method: "DELETE", headers: { "X-Delete-Token": result.delete_token } });
      result.stored = false;
      delete result.delete_token;
      save("result", result);
      clear($("stored-box")).append(el("p", {}, "Deleted. Your saved result has been removed from the database."));
    } catch (err) {
      clear($("stored-box")).append(el("p", {}, err.message));
    }
  }

  /* -------------------------------------------------------------- simulator */
  function renderSimulatorOptions(result) {
    const list = clear($("sim-options"));
    const recByType = Object.fromEntries(result.recommendations.map((r) => [r.finding_type, r]));
    result.findings.forEach((f, index) => {
      list.append(el("li", {}, el("label", {},
        el("input", { type: "checkbox", value: f.finding_type, checked: index < 5 }),
        el("span", {}, f.title, el("span", { class: "to" }, `Fix: ${recByType[f.finding_type]?.recommendation || "use the safest setting"}`)))));
    });
    $("simulator").hidden = result.findings.length === 0;
  }

  function setSelection(mode) {
    [...$("sim-options").querySelectorAll("input")].forEach((box, i) => {
      box.checked = mode === "all" || (mode === "top" && i < 5);
    });
  }

  async function runSimulation() {
    const selected = [...$("sim-options").querySelectorAll("input:checked")].map((b) => b.value);
    if (!selected.length) {
      clear($("sim-result")).append(el("p", { class: "notice" }, "Select at least one finding to simulate."));
      return;
    }
    const button = $("sim-run");
    button.disabled = true;
    try {
      const sim = await api("/api/assessment/simulate-improvement", {
        method: "POST",
        body: { responses: state.responses, fix_findings: selected },
      });
      save("simulation", sim);
      renderSimulation(sim);
    } catch (err) {
      clear($("sim-result")).append(el("p", { class: "notice error" }, err.message));
    } finally {
      button.disabled = false;
    }
  }

  function renderSimulation(sim) {
    const box = clear($("sim-result"));
    box.append(
      el("div", { class: "sim-compare" },
        el("div", {}, el("div", { class: "muted small" }, "Current"), el("div", { class: "num" }, String(sim.current.overall_score)), levelBadge(sim.current.risk_level)),
        el("div", { class: "arrow", "aria-hidden": "true" }, "→"),
        el("div", {}, el("div", { class: "muted small" }, "Simulated"), el("div", { class: "num" }, String(sim.simulated.overall_score)), levelBadge(sim.simulated.risk_level))),
      el("p", { class: "reduction" }, "Risk reduction: ", el("span", { class: "marker" }, `${sim.risk_reduction} points`)),
      el("details", {},
        el("summary", {}, `${sim.changes_applied.length} simulated change${sim.changes_applied.length === 1 ? "" : "s"}`),
        el("ul", { class: "small" }, sim.changes_applied.map((c) => el("li", {}, `${c.question} `, el("strong", {}, `${c.from} → ${c.to}`))))),
      el("p", { class: "disclaimer mt" }, sim.disclaimer));

    const keys = Object.keys(sim.category_changes);
    $("sim-chart-wrap").hidden = false;
    barChart("sim-chart", {
      labels: keys.map((k) => state.labels[k] || k),
      datasets: [
        { label: "Current", data: keys.map((k) => sim.category_changes[k].before), color: App.cssVar("--series-2") },
        { label: "Simulated", data: keys.map((k) => sim.category_changes[k].after), color: App.cssVar("--series-1") },
      ],
      horizontal: true, max: 100, tableHeading: "Category",
    });
  }

  /* -------------------------------------------------------------- wiring */
  async function useDemo() {
    try {
      const demo = await api("/api/demo-profile");
      state.responses = { ...demo.responses };
      save("responses", state.responses);
      goTo(state.categories.length - 1);
    } catch (err) {
      showError(err.message);
    }
  }

  function clearAll() {
    state.responses = {};
    forget();
    goTo(0);
  }

  async function init() {
    $("prev-btn").addEventListener("click", () => goTo(state.current - 1));
    $("next-btn").addEventListener("click", () => goTo(state.current + 1));
    $("submit-btn").addEventListener("click", submit);
    $("demo-btn").addEventListener("click", useDemo);
    $("clear-btn").addEventListener("click", clearAll);
    $("retake-btn").addEventListener("click", () => {
      history.replaceState(null, "", location.pathname);
      $("results").hidden = true;
      $("form-view").hidden = false;
      goTo(0);
    });
    $("sim-run").addEventListener("click", runSimulation);
    $("sim-top").addEventListener("click", () => setSelection("top"));
    $("sim-all").addEventListener("click", () => setSelection("all"));
    $("sim-none").addEventListener("click", () => setSelection("none"));
    $("report-open").addEventListener("click", () => App.openReport(state.responses));
    $("report-download").addEventListener("click", () => App.openReport(state.responses, true));

    try {
      const data = await api("/api/questionnaire");
      state.categories = data.categories;
      const stats = await api("/api/dashboard/stats").catch(() => null);
      state.labels = stats ? stats.category_labels : {};
      // Drop any stored answers for questions that no longer exist.
      const valid = new Set(state.categories.flatMap((c) => c.questions.map((q) => q.id)));
      Object.keys(state.responses).forEach((k) => { if (!valid.has(k)) delete state.responses[k]; });
      renderCategory();

      const previous = load("result");
      if (previous && location.hash === "#results") showResults(previous);
    } catch (err) {
      $("cat-title").textContent = "Couldn't load the questionnaire";
      showError(err.message);
    }
  }

  init();
})();
