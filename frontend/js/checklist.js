/* Printable privacy checklist. Items relevant to your latest findings are flagged.
   Ticks are a per-browser convenience kept in localStorage (never sent anywhere). */
(() => {
  const { el, clear, api, load } = App;
  const KEY = "smpra.checklist";

  function readTicks() {
    try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (err) { return {}; }
  }
  function writeTicks(ticks) {
    try { localStorage.setItem(KEY, JSON.stringify(ticks)); } catch (err) { /* ignore */ }
  }

  async function init() {
    const result = load("result");
    const findings = result ? result.findings.map((f) => f.finding_type) : [];
    const list = document.getElementById("checklist");
    let data;
    try {
      data = await api(`/api/privacy-checklist?findings=${encodeURIComponent(findings.join(","))}`);
    } catch (err) {
      list.replaceWith(el("p", { class: "notice error" }, err.message));
      return;
    }

    const relevant = data.items.filter((i) => i.relevant).length;
    if (result) {
      document.getElementById("checklist-intro").textContent =
        `${relevant} of ${data.items.length} items are flagged as relevant to your latest assessment. Ticks are saved only in this browser.`;
    }

    const ticks = readTicks();
    clear(list);
    data.items.forEach((item) => {
      list.append(el("li", {}, el("label", {},
        el("input", {
          type: "checkbox", checked: Boolean(ticks[item.id]),
          onchange: (e) => { ticks[item.id] = e.target.checked; writeTicks(ticks); },
        }),
        el("div", {},
          el("div", { class: "item" }, item.item, item.relevant ? el("span", { class: "marker flag" }, "relevant to you") : null),
          el("div", { class: "tip" }, item.tip)),
        el("span", { class: "area" }, item.area))));
    });

    document.getElementById("print-btn").addEventListener("click", () => window.print());
    document.getElementById("reset-btn").addEventListener("click", () => {
      writeTicks({});
      list.querySelectorAll("input").forEach((box) => { box.checked = false; });
    });
  }

  init();
})();
