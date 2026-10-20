// Onboarding front end. Every piece of learner or model text is set with textContent, never innerHTML.
"use strict";

const main = document.getElementById("main");
const state = { config: null, id: null, subject: "", pack: "", mission: null, map: null, flagged: new Set(), dropped: new Set() };

function el(tag, attrs, ...kids) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "class") node.className = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else if (k === "text") node.textContent = v;
    else node.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) {
    if (kid === null || kid === undefined || kid === false) continue;
    node.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  }
  return node;
}

function show(...nodes) { main.replaceChildren(...nodes.flat().filter(Boolean)); window.scrollTo(0, 0); }

function setStep(step) {
  const order = ["topic", "mission", "map", "placement", "result"];
  const at = order.indexOf(step);
  document.querySelectorAll("#steps li").forEach((li) => {
    const i = order.indexOf(li.dataset.step);
    li.classList.toggle("on", i === at);
    li.classList.toggle("done", i < at);
    if (i === at) li.setAttribute("aria-current", "step"); else li.removeAttribute("aria-current");
  });
}

function busy(text) { return el("div", { class: "busy", role: "status" }, el("span", { class: "spinner" }), text); }
function errorBox(msg) { return el("div", { class: "error", role: "alert", text: msg }); }

async function api(path, body) {
  const opts = body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const res = await fetch(path, opts);
  let data = {};
  try { data = await res.json(); } catch (_) { /* empty */ }
  if (!res.ok) throw new Error(data.error || `request failed (${res.status})`);
  return data;
}
const sapi = (action, body) => api(`/api/session/${state.id}/${action}`, body === undefined ? {} : body);

// While a request runs, show a spinner. On failure, put the old view back with the error on top.
async function withBusy(text, fn, restore) {
  const before = Array.from(main.childNodes);
  show(busy(text));
  try { return await fn(); }
  catch (e) { main.replaceChildren(errorBox(e.message), ...before); if (restore) restore(); throw e; }
}

// ---------------------------------------------------------------- 1. subject

function topicView() {
  setStep("topic");
  const input = el("input", { type: "text", id: "subject", placeholder: "e.g. statistics for reading research papers", autocomplete: "off" });
  const go = async (pack) => {
    const subject = input.value.trim();
    if (!subject && !pack) { input.focus(); return; }
    try {
      const s = await withBusy("Starting…", () => api("/api/session", { subject, pack: pack || "" }));
      Object.assign(state, { id: s.id, subject: s.subject, pack: s.pack });
      missionView();
    } catch (_) { /* shown */ }
  };
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") go(""); });
  const packs = (state.config.packs || []).map((p) =>
    el("button", { class: "pack", type: "button", onclick: () => go(p.name) },
      el("strong", { text: p.title }), el("span", { class: "small", text: `${p.skills} skills · ${p.description}` })));
  show(
    el("h1", { text: "What do you want to learn?" }),
    el("p", { class: "lede", text: "In about fifteen minutes you'll set a mission, shape a map of the skills it takes, and answer a few questions so your first lesson starts where you actually are." }),
    el("div", { class: "card" },
      el("div", { class: "field" }, el("label", { for: "subject", text: "Subject" }), input),
      el("button", { type: "button", onclick: () => go("") }, "Continue")),
    packs.length ? el("div", {}, el("h2", { text: "Or start from a course pack" }), el("div", { class: "packs" }, packs)) : null,
  );
  input.focus();
}

// ---------------------------------------------------------------- 2. mission

function field(id, label, hint, node) {
  node.id = id;
  return el("div", { class: "field" }, el("label", { for: id, text: label }), hint ? el("p", { class: "hint", text: hint }) : null, node);
}

function missionView(followUp) {
  setStep("mission");
  const prev = state.answers || {};
  const why = el("textarea", {}); why.value = prev.why || "";
  const success = el("textarea", {}); success.value = prev.success || "";
  const deadline = el("input", { type: "text" }); deadline.value = prev.deadline || "";
  const minutes = el("input", { type: "number", min: "5", max: "180", step: "5" }); minutes.value = prev.minutes || state.config.session_minutes;
  const background = el("textarea", {}); background.value = prev.background || "";
  const fu = el("textarea", {});

  const submit = async () => {
    state.answers = { why: why.value, success: success.value, deadline: deadline.value, minutes: minutes.value, background: background.value };
    if (!state.answers.why.trim()) { why.focus(); return; }
    try {
      const out = await withBusy("Reading your answers…", () => sapi("mission", { answers: state.answers, follow_up_answer: fu.value }));
      if (out.follow_up) missionView(out.follow_up);
      else { state.mission = out.mission; missionConfirmView(); }
    } catch (_) { /* shown */ }
  };

  show(
    el("h1", { text: state.subject }),
    el("p", { class: "lede", text: "Every lesson will be built around why you want this. Be concrete: what changes for you once you can do it?" }),
    followUp ? el("div", { class: "card" }, field("followup", followUp, "One more answer and we'll have what we need.", fu)) : null,
    el("div", { class: "card" },
      field("why", "Why do you want to learn this?", "A real situation beats a general wish.", why),
      field("success", "What do you want to be able to do when you're done?", null, success),
      field("deadline", "By when? (optional)", null, deadline),
      field("minutes", "Minutes per session", "Short, regular sessions work best. 25 is the default.", minutes),
      field("background", "What do you already know about it? (optional)", "Placement will check, so there's no need to undersell or oversell.", background),
      el("button", { type: "button", onclick: submit }, "Continue")),
  );
  (followUp ? fu : why).focus();
}

function missionConfirmView() {
  const m = state.mission;
  show(
    el("h1", { text: "Your mission" }),
    el("div", { class: "card" },
      el("p", { class: "mission-why", text: m.why }),
      el("h2", { text: "Success looks like" }),
      el("ul", { class: "plain" }, m.success.map((s) => el("li", { text: s }))),
      m.deadline ? el("p", { class: "small", text: `Deadline: ${m.deadline}` }) : null,
      el("p", { class: "small", text: `Sessions of ${m.session_minutes} minutes.` })),
    el("div", { class: "row" },
      el("button", { type: "button", onclick: mapLoad }, "Looks right, draft my map"),
      el("button", { type: "button", class: "ghost", onclick: () => missionView() }, "Change my answers")),
  );
}

// ---------------------------------------------------------------- 3. map

async function mapLoad() {
  setStep("map");
  try {
    state.map = await withBusy(state.pack ? "Loading the course map…" : "Drafting your skill map. This takes up to a minute…", () => sapi("map"));
    state.flagged = new Set(state.map.flagged); state.dropped = new Set();
    mapView();
  } catch (_) { /* shown */ }
}

function mapView(error) {
  setStep("map");
  const rows = state.map.skills.map((k) => {
    const text = el("textarea", { class: "skilltext", rows: "1", "aria-label": `${k.id} skill` });
    text.value = k.skill;
    text.addEventListener("input", () => { k.skill = text.value; fit(text); });
    const needs = el("input", { type: "text", value: k.needs.join(", "), "aria-label": `${k.id} builds on` });
    needs.addEventListener("input", () => { k.needs = needs.value.split(/[\s,]+/).filter(Boolean); });
    const known = el("input", { type: "checkbox", checked: state.flagged.has(k.id) });
    known.addEventListener("change", () => { known.checked ? state.flagged.add(k.id) : state.flagged.delete(k.id); });
    const row = el("li", { class: "skill" + (state.dropped.has(k.id) ? " dropped" : "") },
      el("span", { class: "sid", text: k.id }), text,
      el("div", { class: "controls" },
        el("label", { class: "check" }, known, "I think I know this"),
        el("span", {}, "builds on ", needs),
        el("button", { type: "button", class: "link", onclick: () => {
          state.dropped.has(k.id) ? state.dropped.delete(k.id) : state.dropped.add(k.id); mapView();
        } }, state.dropped.has(k.id) ? "keep" : "remove")));
    return row;
  });
  const addText = el("input", { type: "text", class: "grow", placeholder: "Add a skill: something you want to be able to do" });
  const add = () => {
    const v = addText.value.trim(); if (!v) return;
    const ids = state.map.skills.map((k) => parseInt(k.id.slice(1), 10)).filter((n) => !isNaN(n));
    state.map.skills.push({ id: `S${(ids.length ? Math.max(...ids) : 0) + 1}`, skill: v, needs: [] });
    mapView();
  };
  addText.addEventListener("keydown", (e) => { if (e.key === "Enter") add(); });

  const confirm = async () => {
    try {
      await withBusy("Saving the map…", () => sapi("map/confirm", {
        skills: state.map.skills, drop: [...state.dropped], flagged: [...state.flagged].filter((f) => !state.dropped.has(f)),
      }));
      placementIntro();
    } catch (_) { /* shown */ }
  };

  const res = state.map.resources || [];
  show(
    error ? errorBox(error) : null,
    el("h1", { text: "Your skill map" }),
    el("p", { class: "lede", text: "Skills run from foundations up to your mission. Edit the wording, remove what you don't need, and tick what you think you know. Ticked skills still get tested; they just come first." }),
    el("div", { class: "card" }, el("ul", { class: "skills" }, rows),
      el("div", { class: "row", style: "margin-top:12px" }, addText, el("button", { type: "button", class: "ghost", onclick: add }, "Add"))),
    res.length ? el("div", {},
      el("h2", { text: "Sources" }),
      el("p", { class: "small", text: state.map.from_pack ? "Chosen for this course." : "Suggested by the model without web search. Your first lessons will check them before citing them." }),
      el("ul", { class: "plain" }, res.map((r) => el("li", {},
        r.url ? el("a", { href: r.url, target: "_blank", rel: "noopener noreferrer", text: r.title }) : el("span", { text: r.title }),
        el("span", { class: "small", text: ` · ${r.use}` }))))) : null,
    el("div", { class: "row", style: "margin-top:24px" }, el("button", { type: "button", onclick: confirm }, "Start placement")),
  );
  main.querySelectorAll("textarea.skilltext").forEach(fit);
}

function fit(area) { area.style.height = "auto"; area.style.height = `${area.scrollHeight + 2}px`; }

// ---------------------------------------------------------------- 4. placement

function placementIntro() {
  setStep("placement");
  show(
    el("h1", { text: "Placement" }),
    el("p", { class: "lede", text: `Up to ${state.config.placement_max_items} short questions. Each one adapts to your last answer, so nobody sees them all.` }),
    el("div", { class: "card" },
      el("ul", { class: "plain" },
        el("li", { text: "Answer from memory in a sentence or two. No notes, no searching." }),
        el("li", { text: "\"I don't know\" is a useful answer. Guessing only puts you in the wrong place." }),
        el("li", { text: "You'll see the model answers at the end, and you can ask for a regrade." }))),
    el("button", { type: "button", onclick: nextQuestion }, "Begin"),
  );
}

async function nextQuestion() {
  setStep("placement");
  try {
    const item = await withBusy("Writing your next question…", () => sapi("placement/next"));
    if (item.done) return resultLoad();
    questionView(item);
  } catch (_) {
    main.append(el("button", { type: "button", onclick: nextQuestion }, "Try again"));
  }
}

function questionView(item) {
  const box = el("textarea", { id: "answer", "aria-label": "Your answer" });
  const send = async (dontKnow) => {
    if (!dontKnow && !box.value.trim()) { box.focus(); return; }
    const answer = box.value;
    try {
      const out = await withBusy("Checking…", () => sapi("placement/answer", { answer, dont_know: dontKnow }), () => { const b = document.getElementById("answer"); if (b) b.value = answer; });
      show(el("p", { class: "verdict " + (out.correct ? "ok" : "no"), text: out.correct ? "Got it." : (dontKnow ? "Noted." : "Not this time.") }));
      setTimeout(nextQuestion, 700);
    } catch (_) { /* shown */ }
  };
  box.addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) send(false); });
  const pct = Math.round(((item.number - 1) / item.max) * 100);
  show(
    el("p", { class: "q-meta", text: `Question ${item.number} · up to ${item.max}` }),
    el("div", { class: "bar", "aria-hidden": "true" }, el("span", { style: `width:${pct}%` })),
    el("p", { class: "question", text: item.question }),
    box,
    el("div", { class: "row", style: "margin-top:14px" },
      el("button", { type: "button", onclick: () => send(false) }, "Submit"),
      el("button", { type: "button", class: "ghost", onclick: () => send(true) }, "I don't know")),
    el("p", { class: "small", style: "margin-top:10px", text: "Ctrl or ⌘ + Enter submits." }),
  );
  box.focus();
}

// ---------------------------------------------------------------- 5. result

async function resultLoad() {
  try { resultView(await withBusy("Placing you on the map…", () => api(`/api/session/${state.id}/summary`))); }
  catch (_) { /* shown */ }
}

function chip(k) {
  if (k.status === "mastered" && k.source === "inferred") return el("span", { class: "chip inferred", text: "known, review tomorrow" });
  if (k.status === "mastered") return el("span", { class: "chip mastered", text: "mastered" });
  if (k.status === "learning") return el("span", { class: "chip learning", text: "learning" });
  return el("span", { class: "chip new", text: "to learn" });
}

function resultView(sum) {
  setStep("result");
  const c = sum.counts;
  const next = sum.skills.find((k) => k.status !== "mastered" && k.needs.every((n) => (sum.skills.find((x) => x.id === n) || {}).status === "mastered"));
  const answers = sum.answers.map((a) => el("div", { class: "answer" },
    el("div", { class: "q", text: a.question }),
    el("dl", {},
      el("dt", { text: "You said" }), el("dd", { text: a.dont_know ? "I don't know" : a.answer }),
      el("dt", { text: "Model answer" }), el("dd", { text: a.key }),
      el("dt", { text: "Result" }), el("dd", {}, a.correct ? (a.disputed ? "Correct (regraded)" : "Correct") : "Not yet",
        a.feedback && !a.dont_know ? el("div", { class: "small", text: a.feedback }) : null,
        !a.correct && !a.dont_know && !sum.saved_to ? el("button", { type: "button", class: "link", onclick: () => dispute(a.index) }, "I was right, regrade this") : null))));

  const save = async () => {
    try {
      const out = await withBusy("Saving your course…", () => sapi("finish"));
      savedView(out.path, next);
    } catch (_) { /* shown */ }
  };

  show(
    el("h1", { text: "Here's where you start" }),
    el("div", { class: "counts" },
      el("div", { class: "count" }, el("b", { text: c.mastered_tested }), el("span", { text: "mastered" })),
      el("div", { class: "count" }, el("b", { text: c.mastered_inferred }), el("span", { text: "known, to confirm" })),
      el("div", { class: "count" }, el("b", { text: c.learning }), el("span", { text: "partly there" })),
      el("div", { class: "count" }, el("b", { text: c.new }), el("span", { text: "to learn" }))),
    next ? el("p", { class: "lede" }, "Your first lesson: ", el("strong", { text: next.skill }), ".") : el("p", { class: "lede", text: "Placement found nothing left to learn on this map. Consider a harder mission." }),
    el("div", { class: "card" }, sum.skills.map((k) => el("div", { class: "result-skill" },
      el("span", {}, el("span", { class: "small", text: `${k.id}  ` }), k.skill), chip(k)))),
    el("h2", { text: "Your answers" }),
    el("div", { class: "card" }, answers.length ? answers : el("p", { class: "small", text: "No questions were needed." })),
    el("div", { class: "row" }, el("button", { type: "button", onclick: save }, "Save my course")),
  );
}

async function dispute(index) {
  try { resultView(await withBusy("Regrading…", () => sapi("placement/dispute", { index }))); }
  catch (_) { /* shown */ }
}

function savedView(path, next) {
  const q = (s) => `"${s.replace(/"/g, '\\"')}"`;
  show(
    el("h1", { text: "Your course is saved" }),
    el("p", { class: "lede" }, "Everything lives in plain files, so any agent with the teach skill can pick it up."),
    el("pre", { text: path }),
    el("h2", { text: "Start lesson 1" }),
    el("p", { text: "Open your agent in that folder and say \"continue my course\". For example:" }),
    el("pre", { text: `cd ${q(path)}\nclaude "continue my course"` }),
    next ? el("p", { class: "small" }, "It will start with: ", el("strong", { text: next.skill }), ".") : null,
    el("p", { class: "small", text: "Short sessions, most days, beat long ones now and then. Your first reviews come due tomorrow." }),
    el("button", { type: "button", class: "ghost", onclick: () => { Object.assign(state, { id: null, mission: null, map: null, answers: null }); topicView(); } }, "Set up another course"),
  );
}

// ---------------------------------------------------------------- boot

(async function boot() {
  try {
    state.config = await api("/api/config");
    document.getElementById("foot").textContent = `Model: ${state.config.model} via ${state.config.provider} · Courses saved to ${state.config.courses_home}`;
    topicView();
  } catch (e) {
    show(errorBox(`Couldn't reach the app: ${e.message}`));
  }
})();
