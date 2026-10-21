/* teach lesson kit 0.3.0: answer boxes, quizzes and a finish panel for HTML lessons.
 *
 * Copy this file and lesson-kit.css into the course's assets/ folder, then in each lesson:
 *   <link rel="stylesheet" href="../assets/lesson-kit.css">
 *   <script defer src="../assets/lesson-kit.js"></script>
 *   <link rel="prev" href="0003-....html">  and  <link rel="next" href="0005-....html">  (optional)
 *   <main data-skill="S3">  (the skill this lesson teaches, from MAP.md)
 *
 * Answer box (one per free-text recall item):
 *   <form data-answer data-prompt="check-1" data-kind="practice|check|review" [data-skill="S3"]
 *         [data-prompt-text="the question, if it is not in the same section"]>
 *     <label for="a1">...</label><textarea id="a1"></textarea>
 *   </form>
 * Quiz (warm-ups only; clicks are light evidence):
 *   <div data-quiz data-explanation="why"><button data-correct="true">..</button>
 *     <button data-correct="false">..</button><p role="status"></p></div>
 * Add data-finish="off" on <main> to leave out the finish panel.
 *
 * Served by `teach-onboard serve`, answers are saved to answers/<lesson>.md and reviewed there.
 * Opened as a plain file, drafts stay in this browser and "Copy for your teacher" copies an
 * entry in the answers format (the teach skill's references/answers-format.md).
 * No dependencies, no network calls except to the server that served the page.
 */
(() => {
  'use strict';
  const main = document.querySelector('main');
  if (!main) return;

  const fileName = decodeURIComponent(location.pathname.split('/').pop() || '');
  const lesson = main.dataset.lesson || fileName.replace(/\.html?$/i, '');
  const pageSkill = main.dataset.skill || '';
  const JUDGMENT = { correct: 'Correct', partial: 'Partly correct', incorrect: 'Not yet correct' };
  const ACTIVE = ['queued', 'running'];

  // ---- helpers -------------------------------------------------------------------
  const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };
  const clean = s => (s || '').replace(/\s+/g, ' ').trim();
  const pad = n => String(n).padStart(2, '0');
  const stamp = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  const quote = s => s.trim().split('\n').map(l => (l.trim() ? '> ' + l : '>')).join('\n');
  const store = {
    get(k) { try { return localStorage.getItem(k) || ''; } catch (e) { return ''; } },
    set(k, v) { try { v ? localStorage.setItem(k, v) : localStorage.removeItem(k); } catch (e) { /* private mode */ } },
  };

  const api = async (path, body) => {
    const opts = body === undefined
      ? { headers: { Accept: 'application/json' } }
      : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
    const r = await fetch('/api/' + path, opts);
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(d.error || r.statusText);
    return d;
  };
  // Served means a teach lesson runner answered, so a plain static server falls back to file mode.
  const served = location.protocol.startsWith('http')
    ? api('ping').then(d => d.teach === true).catch(() => false)
    : Promise.resolve(false);

  const copyText = async (text, fallbackHost) => {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (e) {
      const t = el('textarea', 'kit-copy-area');
      t.value = text;
      t.readOnly = true;
      fallbackHost.append(t);
      t.select();
      let ok = false;
      try { ok = document.execCommand('copy'); } catch (e2) { ok = false; }
      if (ok) t.remove();
      return ok; // when copying is blocked the text stays on screen, selected, for a manual copy
    }
  };

  // ---- quizzes -------------------------------------------------------------------
  document.querySelectorAll('[data-quiz]').forEach((quiz, i) => {
    const status = quiz.querySelector('[role=status]') || quiz.appendChild(el('p', 'kit-quiz-status'));
    status.setAttribute('aria-live', 'polite');
    quiz.querySelectorAll('button[data-correct]').forEach(button => {
      button.type = 'button';
      button.setAttribute('aria-pressed', 'false');
      button.addEventListener('click', () => {
        quiz.querySelectorAll('button[data-correct]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
        const correct = button.dataset.correct === 'true';
        status.textContent = (correct ? 'Yes. ' : 'Not quite. ') + (quiz.dataset.explanation || '');
        quiz.classList.add('kit-answered');
        served.then(ok => ok && api('event', {
          type: 'quiz', lesson, quiz: quiz.dataset.quiz || String(i + 1),
          choice: clean(button.textContent).slice(0, 200), correct,
        }).catch(() => {}));
      });
    });
  });

  // ---- answer boxes --------------------------------------------------------------
  const boxes = [];
  const promptText = form => {
    if (form.dataset.promptText) return form.dataset.promptText.trim();
    const scope = form.closest('section') || form.parentElement;
    const parts = [];
    scope.querySelectorAll('h2, h3, .prompt, ol > li, ul.prompt > li').forEach(n => {
      if (!form.contains(n) && (n.compareDocumentPosition(form) & Node.DOCUMENT_POSITION_FOLLOWING)) parts.push(clean(n.textContent));
    });
    return parts.filter(Boolean).join('\n') || clean(form.querySelector('label')?.textContent) || form.dataset.prompt;
  };
  const labelOf = form => {
    const scope = form.closest('section') || form.parentElement;
    const h = scope.querySelector('h2, h3');
    return clean(h?.textContent) || form.dataset.prompt;
  };

  const entryText = box => [
    `## Answer · ${box.prompt} · ${stamp(new Date())}`, '',
    `Skill: ${box.skill || '-'} · Kind: ${box.kind}`, '',
    '**Prompt**', '', quote(box.promptText), '',
    '**Answer**', '', quote(box.textarea.value), '',
    '*Waiting for teacher feedback.*',
  ].join('\n');

  const renderHistory = (box, items) => {
    const h = box.history;
    h.replaceChildren();
    h.hidden = !items.length;
    if (!items.length) return;
    h.append(el('h3', null, items.length > 1 ? 'Your saved answers' : 'Your saved answer'));
    items.slice().reverse().forEach(it => {
      const d = el('div', 'kit-saved');
      d.append(el('span', 'kit-when', `Saved ${it.when}` + (it.feedback ? '' : ', waiting for your teacher')));
      d.append(el('p', 'kit-answer-text', it.answer));
      if (it.feedback) {
        const f = el('div', 'kit-feedback');
        const head = el('p', 'kit-feedback-head');
        head.append(el('strong', null, 'Teacher feedback'));
        if (it.judgment) head.append(' ', el('span', 'kit-judgment ' + it.judgment, JUDGMENT[it.judgment] || it.judgment));
        const by = [it.feedback_date, it.feedback_by].filter(Boolean).join(', ');
        if (by) head.append(' ', el('span', 'kit-when', by));
        f.append(head);
        it.feedback.split(/\n{2,}/).forEach(p => f.append(el('p', null, p)));
        d.append(f);
      }
      h.append(d);
    });
  };

  document.querySelectorAll('form[data-answer]').forEach(form => {
    const textarea = form.querySelector('textarea');
    if (!textarea || !form.dataset.prompt) return;
    const box = {
      form, textarea,
      prompt: form.dataset.prompt,
      kind: form.dataset.kind || 'practice',
      skill: form.dataset.skill || pageSkill,
      label: labelOf(form),
      promptText: promptText(form),
      key: `teach-answer:${lesson}:${form.dataset.prompt}`,
      saved: [],
    };
    boxes.push(box);
    form.classList.add('kit-answer-box');

    const actions = el('div', 'kit-actions');
    let save = form.querySelector('button[type=submit], button:not([type])');
    if (!save) { save = el('button', null, 'Save my answer'); }
    save.type = 'submit';
    save.classList.add('kit-save');
    const copy = el('button', 'kit-copy', 'Copy for your teacher');
    copy.type = 'button';
    const status = el('span', 'kit-status');
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    actions.append(save, copy, status);
    form.append(actions);
    box.history = el('div', 'kit-history');
    box.history.hidden = true;
    form.append(box.history);
    const say = (text, cls = '') => { status.textContent = text; status.className = 'kit-status ' + cls; };
    box.say = say;

    textarea.value = store.get(box.key);
    textarea.addEventListener('input', () => {
      store.set(box.key, textarea.value);
      say('Draft kept in this browser.');
      document.dispatchEvent(new CustomEvent('teach:draft'));
    });

    copy.addEventListener('click', async () => {
      if (!textarea.value.trim()) { say('Write your answer first.', 'warn'); textarea.focus(); return; }
      const text = `For answers/${lesson}.md:\n\n` + entryText(box);
      say(await copyText(text, form) ? 'Copied. Paste it to your teacher.' : 'Copying is blocked here: select the text below and copy it.', 'ok');
    });

    form.addEventListener('submit', async e => {
      e.preventDefault();
      const answer = textarea.value.trim();
      if (!answer) { say('Write your answer first.', 'warn'); textarea.focus(); return; }
      if (!(await served)) {
        say('Saved in this browser only. Use "Copy for your teacher" and paste it into your chat.', 'warn');
        return;
      }
      save.disabled = true;
      say('Saving...');
      try {
        const d = await api('answer', { lesson, prompt: box.prompt, prompt_text: box.promptText, answer });
        store.set(box.key, '');
        textarea.value = '';
        box.saved = d.answers || [];
        renderHistory(box, box.saved);
        say('Saved to your course. Finish the lesson at the bottom of the page to get feedback.', 'ok');
        document.dispatchEvent(new CustomEvent('teach:changed'));
      } catch (err) {
        say(`Could not save (${err.message}). Your draft is still here.`, 'warn');
      } finally {
        save.disabled = false;
      }
    });

    box.refresh = () => api(`answers?lesson=${encodeURIComponent(lesson)}&prompt=${encodeURIComponent(box.prompt)}`)
      .then(d => { box.saved = d.answers || []; renderHistory(box, box.saved); })
      .catch(() => {});
  });

  served.then(ok => {
    if (ok) boxes.forEach(b => b.refresh());
    else boxes.forEach(b => b.form.classList.add('kit-file-mode'));
  });

  // ---- finish panel --------------------------------------------------------------
  if (main.dataset.finish === 'off') return;
  const panel = el('section', 'kit-finish');
  panel.id = 'finish';
  panel.setAttribute('aria-labelledby', 'kit-finish-title');
  const title = el('h2', null, 'Finish this lesson');
  title.id = 'kit-finish-title';
  const body = el('div', 'kit-finish-body');
  panel.append(title, body);
  main.append(panel);

  const linkRel = rel => {
    const l = document.querySelector(`link[rel="${rel}"]`);
    return l ? { href: l.getAttribute('href'), title: l.getAttribute('title') || l.getAttribute('href').replace(/\.html?$/i, '') } : null;
  };
  const navLink = (cls, small, item) => {
    const a = el('a', cls);
    a.href = item.href;
    a.append(el('span', 'kit-small', small), el('span', null, item.title));
    return a;
  };
  const nav = (prev, next, course) => {
    const n = el('nav', 'kit-nav');
    n.setAttribute('aria-label', 'Lesson navigation');
    if (prev) n.append(navLink('kit-prev', 'Previous lesson', prev));
    n.append(navLink('kit-course', 'Course', course));
    if (next) n.append(navLink('kit-next', 'Next lesson', next));
    return n;
  };
  const promptList = rows => {
    const ul = el('ul', 'kit-prompts');
    rows.forEach(r => {
      const li = el('li', r.state);
      li.append(el('span', 'kit-dot'));
      const t = el('span', 'kit-label');
      t.append(el('strong', null, r.label), el('span', 'kit-small', r.note));
      li.append(t);
      if (r.judgment) li.append(el('span', 'kit-judgment ' + r.judgment, JUDGMENT[r.judgment] || r.judgment));
      if (r.form) {
        const go = el('button', 'kit-link', r.state === 'todo' ? 'Answer' : 'View');
        go.type = 'button';
        go.onclick = () => r.form.scrollIntoView({ behavior: 'smooth', block: 'center' });
        li.append(go);
      }
      ul.append(li);
    });
    if (!rows.length) ul.append(el('li', 'todo', 'This lesson has no answer boxes.'));
    return ul;
  };
  const formFor = prompt => boxes.find(b => b.prompt === prompt)?.form;

  // File mode: what is drafted here, one button to copy it all, links from <link rel>.
  const renderFile = () => {
    body.replaceChildren();
    body.append(promptList(boxes.map(b => ({
      label: b.label, form: b.form,
      state: b.textarea.value.trim() ? 'draft' : 'todo',
      note: b.textarea.value.trim() ? 'Draft in this browser' : 'No answer yet',
    }))));
    const actions = el('div', 'kit-finish-actions');
    const b = el('button', 'kit-primary', 'Copy all answers for your teacher');
    b.type = 'button';
    const note = el('span', 'kit-status', 'Paste them into your chat with your teacher, who files them and writes feedback. To save answers here instead, open the course with teach-onboard serve.');
    b.onclick = async () => {
      const done = boxes.filter(x => x.textarea.value.trim());
      if (!done.length) { note.textContent = 'Write at least one answer first.'; return; }
      const text = `For answers/${lesson}.md:\n\n` + done.map(entryText).join('\n\n');
      note.textContent = await copyText(text, actions) ? `Copied ${done.length} answer${done.length > 1 ? 's' : ''}. Paste them to your teacher.` : 'Copying is blocked here: select the text below and copy it.';
    };
    actions.append(b, note);
    body.append(actions, nav(linkRel('prev'), linkRel('next'), { href: '../MAP.md', title: 'Skill map and progress' }));
  };

  // Served mode: state comes from the runner, jobs run in the background and survive a reload.
  let state = null;
  let timer = null;
  const poll = id => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      try {
        const j = await api(`jobs/${id}`);
        if (ACTIVE.includes(j.status)) {
          const p = panel.querySelector(`[data-job="${id}"] .kit-job-text`);
          if (p) p.textContent = j.progress || 'Working';
          poll(id);
        } else {
          await load();
          boxes.forEach(b => b.refresh());
        }
      } catch (e) { poll(id); }
    }, 2000);
  };
  const jobLine = j => {
    const p = el('p', 'kit-job');
    p.dataset.job = j.id;
    p.append(el('span', 'kit-spinner'), el('span', 'kit-job-text', j.progress || 'Working'));
    return p;
  };
  const startJob = async (button, note, path) => {
    button.disabled = true;
    note.textContent = 'Starting...';
    try {
      const d = await api(path, { lesson });
      await load();
      if (d.job) poll(d.job.id);
    } catch (e) {
      note.textContent = e.message;
      note.className = 'kit-status warn';
      button.disabled = false;
    }
  };

  const renderServed = () => {
    const s = state;
    body.replaceChildren();
    body.append(promptList(s.prompts.map(p => ({
      label: p.label, form: formFor(p.prompt), judgment: p.judgment,
      state: p.reviewed ? 'reviewed' : p.saved ? 'saved' : 'todo',
      note: p.reviewed ? `Saved ${p.when}, feedback ready` : p.saved ? `Saved ${p.when}, waiting for feedback` : 'No answer saved yet',
    }))));

    const actions = el('div', 'kit-finish-actions');
    const rj = s.review_job;
    if (rj && ACTIVE.includes(rj.status)) {
      actions.append(jobLine(rj));
      poll(rj.id);
    } else {
      const b = el('button', 'kit-primary', 'Finish and get feedback');
      b.type = 'button';
      const note = el('span', 'kit-status', s.pending > 0
        ? 'Your teacher reads your saved answers and writes feedback under each one.'
        : s.answers ? 'Every saved answer has feedback. Save a new answer to get more.' : 'Save an answer above first. Feedback is on what you write.');
      b.disabled = !(s.pending > 0);
      b.onclick = () => startJob(b, note, 'review');
      actions.append(b, note);
      if (rj && rj.status === 'failed') actions.append(el('p', 'kit-status warn', `The last review stopped: ${rj.error || 'unknown error'}`));
    }
    body.append(actions);

    const R = s.last_review;
    if (R && !(rj && ACTIVE.includes(rj.status))) {
      const box = el('div', 'kit-result');
      box.append(el('h3', null, `Feedback from your teacher (${R.date})`));
      if (R.summary) box.append(el('p', null, R.summary));
      if (R.map_changes && R.map_changes.length) {
        box.append(el('h4', null, 'Your skill map'));
        const ul = el('ul');
        R.map_changes.forEach(c => ul.append(el('li', null, c)));
        box.append(ul);
      }
      if (R.learning_record) box.append(el('p', 'kit-small', `Learning record saved: ${R.learning_record}`));
      box.append(el('p', 'kit-small', 'Detailed feedback is under each saved answer above.'));
      body.append(box);
    }

    body.append(nav(s.prev, s.next, { href: s.course_href || '/', title: 'All lessons and progress' }));

    if (!s.next) {
      const prep = el('div', 'kit-finish-actions');
      const dj = s.draft_job;
      if (dj && ACTIVE.includes(dj.status)) {
        prep.append(jobLine(dj));
        poll(dj.id);
      } else {
        const b = el('button', 'kit-secondary', 'Draft my next lesson');
        b.type = 'button';
        const ready = s.status === 'reviewed';
        b.disabled = !ready;
        const note = el('span', 'kit-status', ready
          ? 'A model drafts the next lesson from your map and feedback, citing only sources it retrieved. It stays labelled AI-drafted until a person checks the sources.'
          : 'Available once your answers have feedback, so the next lesson builds on what you showed.');
        b.onclick = () => startJob(b, note, 'draft');
        prep.append(b, note);
        if (dj && dj.status === 'failed') prep.append(el('p', 'kit-status warn', `The last draft stopped: ${dj.error || 'unknown error'}`));
      }
      body.append(prep);
    }
  };

  const load = async () => {
    try {
      state = await api(`lesson?lesson=${encodeURIComponent(lesson)}`);
      renderServed();
    } catch (e) {
      body.replaceChildren(el('p', 'kit-status warn', `Could not load your progress (${e.message}). Reload the page to try again.`));
    }
  };

  served.then(ok => {
    if (ok) {
      document.addEventListener('teach:changed', () => load());
      load();
    } else {
      renderFile();
      document.addEventListener('teach:draft', renderFile);
    }
  });
})();
