/* Model explorer for "The absent stakeholder". Plain JavaScript, no dependencies.
   Data: summary.json (scores, flags, criterion pass rates) and items_<model>.json (each answer with its verdicts and labels),
   built by research/post1-analysis/scripts/s11_explorer_data.py. Nothing is sent anywhere; nothing is stored. */
(function () {
  "use strict";
  const root = document.getElementById("mx");
  if (!root) return;
  const base = root.getAttribute("data-base") || "explorer/";
  const DATA = "https://github.com/azin-nazari/azin-nazari.github.io/tree/main/research/post1-analysis/10-models";
  const JUDGE = {
    "Claude Haiku 5.5": { cls: "j-haiku", mark: "●" },
    "GPT-6 Luna": { cls: "j-luna", mark: "■" },
    "Jev 1.13": { cls: "j-jev", mark: "◆" },
    "Gemini 3.5 Flash-Lite": { cls: "j-flash", mark: "▲" },
  };
  const LABELLERS = ["Claude Haiku 5.5", "GPT-6 Luna"];
  const S_MIN = 40, S_MAX = 85, F_MAX = 60;
  const state = { scorer: "panel", labeller: "both", model: null, items: {}, filter: "all", item: null };
  let S = null;

  const el = (tag, attrs, ...kids) => {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (k === "class") n.className = v;
      else if (k === "text") n.textContent = v;
      else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
      else if (v !== null && v !== undefined && v !== false) n.setAttribute(k, v === true ? "" : v);
    }
    for (const k of kids.flat()) if (k !== null && k !== undefined && k !== false) n.append(k.nodeType ? k : document.createTextNode(String(k)));
    return n;
  };
  const pct = (x, lo, hi) => `${Math.max(0, Math.min(100, ((x - lo) / (hi - lo)) * 100))}%`;
  const f1 = (x) => (x === null || x === undefined ? "–" : Number(x).toFixed(1));
  const f0 = (x) => (x === null || x === undefined ? "–" : Math.round(Number(x)).toString());
  const scorerLabel = (k) => S.scorers.find((s) => s.key === k).label;
  const rationales = {};

  // Minimal, safe Markdown: the text is escaped first, then only headings, emphasis, code, lists and paragraphs become tags.
  function md(text) {
    const esc = (t) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const inline = (t) => esc(t).replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<em>$2</em>").replace(/__([^_]+)__/g, "<strong>$1</strong>");
    const out = []; let list = null, para = [];
    const flush = () => { if (para.length) { out.push(`<p>${inline(para.join(" "))}</p>`); para = []; } };
    const close = () => { if (list) { out.push(`</${list}>`); list = null; } };
    const lines = String(text).split("\n");
    const nextItemKind = (i) => { for (let k = i + 1; k < lines.length; k++) { const t = lines[k].trim(); if (!t) continue;
      return /^\d+[.)]\s/.test(t) ? "ol" : /^[-*•]\s/.test(t) ? "ul" : null; } return null; };
    for (let i = 0; i < lines.length; i++) {
      const raw = lines[i];
      const line = raw.trimEnd();
      let m;
      if (!line.trim()) { flush(); if (list && nextItemKind(i) !== list) close(); continue; }
      if ((m = line.match(/^\s*(#{1,6})\s+(.*)$/))) { flush(); close(); out.push(`<p class="mx-md-h">${inline(m[2])}</p>`); continue; }
      if (/^\s*(-{3,}|\*{3,})\s*$/.test(line)) { flush(); close(); out.push("<hr>"); continue; }
      if ((m = line.match(/^\s*[-*•]\s+(.*)$/)) || (m = line.match(/^\s*(\d+)[.)]\s+(.*)$/))) {
        flush(); const kind = /^\s*\d/.test(line) ? "ol" : "ul";
        const num = kind === "ol" ? Number(m[1]) : null, body = kind === "ol" ? m[2] : m[1];
        if (list !== kind) { close(); out.push(kind === "ol" && num > 1 ? `<ol start="${num}">` : `<${kind}>`); list = kind; }
        out.push(`<li>${inline(body)}</li>`); continue;
      }
      if (list && /^\s{2,}\S/.test(raw)) { out[out.length - 1] = out[out.length - 1].replace(/<\/li>$/, " " + inline(line.trim()) + "</li>"); continue; }
      close(); para.push(line.trim());
    }
    flush(); close();
    const div = document.createElement("div"); div.className = "mx-md"; div.innerHTML = out.join(""); return div;
  }

  function controls() {
    const sel = el("select", { id: "mx-scorer", "aria-label": "Which judge's ANIMA score to show", onchange: (e) => { state.scorer = e.target.value; render(); } },
      S.scorers.map((s) => el("option", { value: s.key, selected: s.key === state.scorer },
        s.label + (s.models_graded.length < S.models.length ? ` (${s.models_graded.length} of ${S.models.length} models)` : ""))));
    const seg = el("div", { class: "mx-seg", role: "group", "aria-label": "Which labeller's moralizing flags to emphasize" },
      [["both", "Both labellers"], ["Claude Haiku 5.5", "Claude Haiku 5.5"], ["GPT-6 Luna", "GPT-6 Luna"]].map(([k, t]) =>
        el("button", { type: "button", "aria-pressed": String(state.labeller === k), onclick: () => { state.labeller = k; render(); } }, t)));
    const dl = el("button", { type: "button", class: "mx-ghost", onclick: downloadCsv }, "Download this view (CSV)");
    return el("div", { class: "mx-controls" },
      el("label", { class: "mx-ctl" }, el("span", { text: "ANIMA score from" }), sel),
      el("div", { class: "mx-ctl" }, el("span", { text: "Moralizing flags from" }), seg),
      dl);
  }

  function legend() {
    return el("div", { class: "mx-legend", "aria-hidden": "true" },
      el("span", {}, el("i", { class: "mx-key-bar" }), " ANIMA score, 95% interval"),
      el("span", { class: "j-haiku" }, el("b", { text: "●" }), " moralizing flags by Claude Haiku 5.5"),
      el("span", { class: "j-luna" }, el("b", { text: "■" }), " moralizing flags by GPT-6 Luna"),
      el("span", { class: "mx-scale" }, `Score track ${S_MIN}–${S_MAX}; flag track 0–${F_MAX}%`));
  }

  function chart() {
    const sc = S.scores[state.scorer] || {};
    const rows = S.models.map((m) => {
      const s = sc[m.name];
      const fl = S.flags[m.name] || {};
      const scoreCell = s
        ? el("div", { class: "mx-track", title: `${m.name}: ${f1(s.score)} (95% interval ${f1(s.lo)} to ${f1(s.hi)})` },
            el("i", { class: "mx-ci", style: `left:${pct(s.lo, S_MIN, S_MAX)};right:calc(100% - ${pct(s.hi, S_MIN, S_MAX)})` }),
            el("i", { class: "mx-dot", style: `left:${pct(s.score, S_MIN, S_MAX)}` }),
            el("span", { class: "mx-val", style: `left:${pct(s.hi, S_MIN, S_MAX)}` }, f1(s.score)))
        : el("div", { class: "mx-track mx-missing" }, "not graded by this judge");
      const flagCell = el("div", { class: "mx-track mx-ftrack" },
        LABELLERS.map((j, k) => {
          const d = fl[j];
          if (!d) return null;
          const dim = state.labeller !== "both" && state.labeller !== j;
          return el("span", { class: `mx-flag ${JUDGE[j].cls}${dim ? " mx-dim" : ""}`, style: `top:${k === 0 ? 30 : 64}%`,
            title: `${j}: ${f0(d.share)}% of ${d.n} answers flagged (95% interval ${f0(d.lo)} to ${f0(d.hi)}%)` },
            el("i", { class: "mx-fci", style: `left:${pct(d.lo, 0, F_MAX)};right:calc(100% - ${pct(d.hi, 0, F_MAX)})` }),
            el("b", { style: `left:${pct(d.share, 0, F_MAX)}` }, JUDGE[j].mark));
        }));
      const flagText = LABELLERS.filter((j) => fl[j] && (state.labeller === "both" || state.labeller === j)).map((j) => `${f0(fl[j].share)}%`).join(" / ");
      const selected = state.model === m.name;
      return el("button", { type: "button", class: "mx-row" + (selected ? " mx-sel" : ""), "aria-pressed": String(selected),
        "aria-label": `${m.name}. ${s ? `ANIMA ${f1(s.score)}` : "not graded"}; flagged ${flagText}. Show evidence.`,
        onclick: () => { state.model = selected ? null : m.name; state.item = null; state.filter = "all"; render(); if (state.model) loadItems(m); } },
        el("span", { class: "mx-name" }, el("b", { text: m.name }), el("small", { text: `${m.developer} · ${m.weights}` })),
        scoreCell,
        el("span", { class: "mx-ftext" }, flagText),
        flagCell);
    });
    const axis = (lo, hi, ticks, unit) => el("div", { class: "mx-axis" }, ticks.map((t) => el("span", { style: `left:${pct(t, lo, hi)}` }, `${t}${unit}`)));
    return el("div", { class: "mx-chart" },
      el("div", { class: "mx-head" }, el("span", {}, "Model"), el("span", {}, "ANIMA score (0–100)"), el("span", {}, ""), el("span", { title: "Share of answers a labeller judged to add moral commentary the user did not ask for and the answer does not need" }, "Flagged for moralizing")),
      rows,
      el("div", { class: "mx-foot" }, el("span", {}), axis(S_MIN, S_MAX, [40, 50, 60, 70, 80], ""), el("span", {}), axis(0, F_MAX, [0, 20, 40, 60], "%")));
  }

  function evidence() {
    if (!state.model) return el("p", { class: "mx-hint" }, "Select a model to see its numbers, criterion by criterion, and every answer it gave.");
    const m = S.models.find((x) => x.name === state.model);
    const fl = S.flags[m.name] || {};
    const scoreRows = S.scorers.map((s) => {
      const d = (S.scores[s.key] || {})[m.name];
      return el("tr", { class: s.key === state.scorer ? "mx-cur" : "" }, el("th", { scope: "row", text: s.key === "panel" ? "Panel (Haiku + Flash-Lite)" : s.label }),
        el("td", {}, d ? `${f1(d.score)} (${f1(d.lo)} to ${f1(d.hi)})` : "not graded"),
        el("td", {}, d && d.rank ? `${d.rank} of 6 (${d.rank_lo}–${d.rank_hi})` : "–"));
    });
    const flagRows = LABELLERS.map((j) => {
      const d = fl[j];
      return el("tr", {}, el("th", { scope: "row" }, el("span", { class: JUDGE[j].cls, text: JUDGE[j].mark + " " }), j),
        el("td", {}, d ? `${f0(d.share)}% (${f0(d.lo)} to ${f0(d.hi)}%)` : "–"), el("td", {}, d ? `${d.n}` : "–"),
        el("td", {}, d ? `${f0(d.completes)}%` : "–"), el("td", {}, d ? `${d.bare_refusals}` : "–"));
    });
    const words = (fl["Claude Haiku 5.5"] || {}).words;
    const crit = (S.criteria[state.scorer] || {})[m.name];
    let critBlock;
    if (!crit) critBlock = el("p", { class: "mx-hint" }, `${scorerLabel(state.scorer)} did not grade this model.`);
    else {
      const all = S.criteria[state.scorer];
      const avg = (c) => { const v = Object.values(all).map((x) => x[c] && x[c].rate).filter((x) => x !== undefined && x !== null); return v.reduce((a, b) => a + b, 0) / v.length; };
      const list = Object.entries(crit).sort((a, b) => b[1].n - a[1].n);
      critBlock = el("table", { class: "mx-table" },
        el("caption", {}, `Share of verdicts passed, ${scorerLabel(state.scorer)}; the bar marks this model, the tick the mean over the models this scorer graded.`),
        el("thead", {}, el("tr", {}, el("th", { scope: "col" }, "Criterion"), el("th", { scope: "col" }, "Verdicts"), el("th", { scope: "col" }, "Passed"), el("th", { scope: "col", class: "mx-wide" }, ""))),
        el("tbody", {}, list.map(([c, d]) => {
          const a = avg(c);
          return el("tr", {}, el("th", { scope: "row", text: c }), el("td", {}, d.n), el("td", {}, `${f0(d.rate)}%`),
            el("td", { class: "mx-wide" }, el("div", { class: "mx-mini" }, el("i", { style: `width:${d.rate}%` }), el("u", { style: `left:${a}%`, title: `mean ${f0(a)}%` }))));
        })));
    }
    return el("div", { class: "mx-evidence", role: "region", "aria-label": `Evidence for ${m.name}` },
      el("h4", {}, m.name, el("small", { text: ` ${m.developer} · ${m.weights} · OpenRouter id ${m.openrouter}` })),
      m.note ? el("p", { class: "mx-note" }, `Note: ${m.note}.`) : null,
      el("p", { class: "mx-note" }, S.settings + (words ? ` Mean answer length ${words} words.` : "")),
      el("div", { class: "mx-cols" },
        el("table", { class: "mx-table" }, el("caption", {}, "ANIMA score by scorer, 95% interval and rank range from resampling questions"),
          el("thead", {}, el("tr", {}, el("th", { scope: "col" }, "Scorer"), el("th", { scope: "col" }, "Score"), el("th", { scope: "col" }, "Rank"))),
          el("tbody", {}, scoreRows)),
        el("table", { class: "mx-table" }, el("caption", {}, "Moralizing labels from two judges on the same answers (not part of ANIMA)"),
          el("thead", {}, el("tr", {}, el("th", { scope: "col" }, "Labeller"), el("th", { scope: "col" }, "Flagged for moralizing"), el("th", { scope: "col" }, "Answers"),
            el("th", { scope: "col" }, "Attempted the task"), el("th", { scope: "col" }, "Bare refusals"))),
          el("tbody", {}, flagRows))),
      critBlock,
      responses(m));
  }

  function responses(m) {
    const items = state.items[m.slug];
    const box = el("div", { class: "mx-resp" }, el("h5", { text: "Every answer" }));
    if (!items) { box.append(el("p", { class: "mx-hint" }, "Loading answers…")); return box; }
    const flagged = (it, n) => LABELLERS.filter((j) => it.labels[j] && it.labels[j].moralizing === "yes").length === n;
    const filters = { all: ["All", () => true], both: ["Flagged by both labellers", (it) => flagged(it, 2)],
      one: ["Labellers disagree", (it) => flagged(it, 1)], low: ["ANIMA score below 50", (it) => it.score !== null && it.score < 50],
      jev: ["Jev disagrees with both inline judges", (it) => Object.values(it.criteria).some((c) => c["Jev 1.13"] !== undefined &&
        (c["Claude Haiku 5.5"] === 0 || c["Claude Haiku 5.5"] === 1) && c["Claude Haiku 5.5"] === c["Gemini 3.5 Flash-Lite"] &&
        (c["Jev 1.13"] >= 0.5 ? 1 : 0) !== c["Claude Haiku 5.5"])] };
    const shown = items.filter(filters[state.filter][1]);
    box.append(el("div", { class: "mx-seg mx-filters", role: "group", "aria-label": "Filter answers" },
      Object.entries(filters).map(([k, [t, fn]]) => el("button", { type: "button", "aria-pressed": String(state.filter === k),
        onclick: () => { state.filter = k; state.item = null; render(); } }, `${t} (${items.filter(fn).length})`))));
    if (!shown.length) { box.append(el("p", { class: "mx-hint" }, "No answers match.")); return box; }
    const cur = shown.find((x) => x.id === state.item) || shown[0];
    box.append(el("label", { class: "mx-ctl mx-qsel" }, el("span", { text: "Question" }),
      el("select", { "aria-label": "Choose a question", onchange: (e) => { state.item = Number(e.target.value); render(); } },
        shown.map((it) => el("option", { value: it.id, selected: it.id === cur.id },
          `#${it.id} · ${it.lang} · ${(it.q_en || it.q).replace(/\s*Answer:\s*$/, "").slice(0, 80)}`)))));
    box.append(item(cur));
    return box;
  }

  function item(it) {
    const crit = Object.entries(it.criteria);
    const judges = Object.keys(JUDGE).filter((j) => crit.some(([, c]) => c[j] !== undefined));
    const cell = (j, v) => {
      if (v === undefined) return el("td", { class: "mx-na" }, "–");
      if (j === "Jev 1.13") { const pass = v >= 0.5; return el("td", { class: pass ? "mx-pass" : "mx-fail" }, `${pass ? "pass" : "fail"} (P ${v.toFixed(2)})`); }
      if (v === 1) return el("td", { class: "mx-pass" }, "pass");
      if (v === 0) return el("td", { class: "mx-fail" }, "fail");
      return el("td", {}, `${Math.round(v * 100)}% pass`);
    };
    const q = it.q.replace(/\s*Answer:\s*$/, "");
    return el("div", { class: "mx-item" },
      el("div", { class: "ex ex-prompt" }, el("span", { class: "ex-label" }, `Prompt · ANIMA question ${it.id} · ${it.lang}`), el("p", {}, q),
        it.q_en && it.lang !== "English" ? el("p", { class: "mx-tr" }, "English (from the dataset): ", it.q_en.replace(/\s*Answer:\s*$/, "")) : null,
        /Answer:\s*$/.test(it.q) ? el("p", { class: "mx-note" }, "The dataset's prompt ends with the template marker ", el("code", {}, "Answer:"), ", sent as is.") : null),
      el("details", { class: "ex ex-answer", open: it.words <= 250 },
        el("summary", {}, el("span", { class: "ex-label" }, `Answer · ${it.words} words · original language, not translated`)),
        el("div", { class: "mx-answer" }, md(it.answer))),
      el("div", { class: "ex ex-verdict" },
        el("span", { class: "ex-label" }, `Verdicts · ANIMA score ${it.score === null ? "–" : f0(it.score)} from the panel (votes averaged)`),
        el("div", { class: "table-responsive" }, el("table", { class: "mx-table" },
          el("thead", {}, el("tr", {}, el("th", { scope: "col" }, "Criterion"), judges.map((j) => el("th", { scope: "col" }, el("span", { class: JUDGE[j].cls, text: JUDGE[j].mark + " " }), j === "Jev 1.13" ? "Jev 1.13 (probability)" : j)))),
          el("tbody", {}, crit.map(([c, v]) => el("tr", {}, el("th", { scope: "row", text: c }), judges.map((j) => cell(j, v[j]))))))),
        whyBlock(it),
        el("ul", { class: "mx-labels" }, LABELLERS.map((j) => {
          const l = it.labels[j];
          if (!l) return el("li", {}, `${j}: no label`);
          return el("li", {}, el("span", { class: JUDGE[j].cls, text: JUDGE[j].mark + " " }), el("b", { text: `${j}: ` }),
            l.moralizing === "yes" ? "flagged for moralizing. " : "not flagged. ", l.refusal === "yes" ? "Bare refusal. " : "", el("q", {}, l.reason));
        }))));
  }

  function whyBlock(it) {
    const m = S.models.find((x) => x.name === state.model);
    const r = m && rationales[m.slug];
    if (!r) return el("p", { class: "mx-note" }, "Loading the judges' reasoning…");
    const per = r[String(it.id)];
    if (!per) return el("p", { class: "mx-note" }, "No written reasoning saved for this answer.");
    return el("div", { class: "mx-why" },
      el("p", { class: "mx-note" }, "Each panel judge explains its verdict before giving it. GPT-6 Luna's re-grade kept verdicts only; Jev 1.13 returns a probability without text."),
      Object.entries(per).flatMap(([crit, vsets]) => Object.entries(vsets).map(([vs, byJudge]) =>
        el("details", { class: "mx-whyc" },
          el("summary", {}, `Why: ${crit}${Object.keys(vsets).length > 1 ? ` (variant ${Number(vs) + 1})` : ""}`),
          ["Claude Haiku 5.5", "Gemini 3.5 Flash-Lite"].filter((j) => byJudge[j]).map((j) =>
            el("div", { class: "mx-whyj" }, el("b", {}, el("span", { class: JUDGE[j].cls, text: JUDGE[j].mark + " " }), j), md(byJudge[j])))))));
  }

  async function loadItems(m) {
    if (state.items[m.slug]) return;
    try {
      const r = await fetch(`${base}items_${m.slug}.json`);
      state.items[m.slug] = await r.json();
    } catch (e) {
      state.items[m.slug] = [];
    }
    render();
    try {
      const r = await fetch(`${base}rationales_${m.slug}.json`);
      rationales[m.slug] = await r.json();
    } catch (e) {
      rationales[m.slug] = {};
    }
    render();
  }

  function downloadCsv() {
    const sc = S.scores[state.scorer] || {};
    const lines = [["model", "developer", "scorer", "anima_score", "ci_low", "ci_high", "rank", "rank_low", "rank_high", "flagged_haiku_pct", "flagged_luna_pct"].join(",")];
    for (const m of S.models) {
      const s = sc[m.name] || {};
      const fl = S.flags[m.name] || {};
      lines.push([m.name, m.developer, scorerLabel(state.scorer), s.score ?? "", s.lo ?? "", s.hi ?? "", s.rank ?? "", s.rank_lo ?? "", s.rank_hi ?? "",
        fl["Claude Haiku 5.5"] ? fl["Claude Haiku 5.5"].share : "", fl["GPT-6 Luna"] ? fl["GPT-6 Luna"].share : ""].map((x) => `"${String(x).replace(/"/g, '""')}"`).join(","));
    }
    const a = el("a", { href: URL.createObjectURL(new Blob([lines.join("\n")], { type: "text/csv" })), download: "six-models-view.csv" });
    document.body.append(a); a.click(); a.remove();
  }

  function render() {
    const focusId = document.activeElement && document.activeElement.closest && document.activeElement.closest("#mx") ? document.activeElement.textContent : null;
    root.replaceChildren(
      el("p", { class: "mx-title" }, el("b", { text: "Six models, two different measurements" }), el("span", { text: " · select a model to see every answer behind its numbers" })),
      controls(), legend(), chart(),
      el("p", { class: "mx-scope" }, "Six model versions, 114 ANIMA questions, one answer each. The panel's two votes are averaged per criterion (a split counts as half). Moralizing flags are two judges' labels, not verified errors. ",
        el("a", { href: "#methods-limitations-and-data" }, "How I measured this"), " · ", el("a", { href: DATA }, "all data")),
      el("div", { "aria-live": "polite" }, evidence()));
    if (focusId) { const b = [...root.querySelectorAll("button")].find((x) => x.textContent === focusId); if (b) b.focus(); }
  }

  fetch(base + "summary.json").then((r) => r.json()).then((d) => {
    S = d;
    root.classList.add("mx-live");
    render();
  }).catch(() => { root.classList.add("mx-failed"); });
})();
