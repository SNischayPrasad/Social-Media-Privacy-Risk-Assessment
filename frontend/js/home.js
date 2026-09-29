/* Landing page: the self-redacting demo profile and the category grid. */
(() => {
  const { el, clear, levelBadge } = App;

  // Before / after states for the fictional demo profile.
  // Scores come from the real engine: python tools/run_demo.py -> 82 CRITICAL -> 53 HIGH.
  const BEFORE = { score: 82, level: "CRITICAL" };
  const AFTER = { score: 53, level: "HIGH" };
  const EXPOSURE_TEXT = ["Visible to everyone", "Visible to everyone", "Visible to everyone", "Broadcast live", "Posted in advance"];

  const rows = [...document.querySelectorAll("#specimen-rows .state")];
  const toggle = document.getElementById("specimen-toggle");
  const scoreNode = document.getElementById("specimen-score");
  const levelNode = document.getElementById("specimen-level");

  function render(reviewed) {
    let exposureIndex = 0;
    rows.forEach((node) => {
      clear(node);
      if (node.dataset.kind === "exposure") {
        const text = EXPOSURE_TEXT[exposureIndex++];
        node.append(reviewed
          ? el("span", {}, el("span", { class: "redacted", "aria-hidden": "true" }, "hidden hidden"), " only me")
          : el("span", { class: "marker" }, text));
      } else {
        node.append(reviewed ? el("span", {}, "On") : el("span", { class: "marker" }, "Off"));
      }
    });
    const state = reviewed ? AFTER : BEFORE;
    clear(scoreNode).append(String(state.score), el("small", {}, "/100"));
    clear(levelNode).append(levelBadge(state.level));
  }

  toggle.addEventListener("change", () => render(toggle.checked));
  render(false);

  // Category grid - loaded from the API so it always matches the backend weights.
  const grid = document.getElementById("category-grid");
  App.api("/api/questionnaire").then((data) => {
    data.categories.forEach((cat) => {
      grid.append(el("div", {},
        el("div", { class: "code" }, `Category ${cat.code} · ${cat.questions.length} questions`),
        el("div", { class: "name" }, cat.name),
        el("div", { class: "weight" }, `Weight ${cat.weight}%`)));
    });
  }).catch((err) => grid.replaceWith(el("p", { class: "notice error" }, err.message)));
})();
