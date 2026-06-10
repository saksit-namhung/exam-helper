// =============================================================================
// EXAM PRACTICE APP — app.js
// =============================================================================

// ── Helpers ──────────────────────────────────────────────────────────────────

const el  = (id) => document.getElementById(id);
const esc = (s)  => String(s ?? '')
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const norm = (s) => String(s ?? '').toLowerCase().trim().replace(/\.+$/, '');

// ── State ────────────────────────────────────────────────────────────────────

const state = {
  exams:            [],    // [{filename, name, code, total_questions}]
  selectedExam:     null,
  allQuestions:     [],
  sessionQuestions: [],
  currentIdx:       0,
  results:          [],    // [{question, userAnswer, isCorrect, skipped, hasAnswer}]
  retryMode:        false,
  // Ordering UI internal state
  _ordering:        [],    // [{idx, val}] – selected items in click order
};

// ── Screen management ─────────────────────────────────────────────────────────

const SCREENS = ['home','setup','question','feedback','summary'];

function showScreen(name) {
  SCREENS.forEach(s => {
    const div = el(`screen-${s}`);
    if (div) div.classList.toggle('hidden', s !== name);
  });
  window.scrollTo(0, 0);
}

// ── Question type detection ───────────────────────────────────────────────────

/**
 * Returns one of:
 *   'mc-single'         – radio buttons (A/B/C/D, one correct)
 *   'mc-multiple'       – checkboxes (A/B/C/D, many correct)
 *   'hs-selection'      – checkboxes from bullet list (no order)
 *   'hs-ordering'       – click-to-order from bullet list
 *   'hs-matching'       – dropdown per statement
 *   'hs-multi-slot'     – N dropdowns, same option may be chosen multiple times
 *   'hs-noanswer'       – hotspot but answer missing in source
 *   'mc-noanswer'       – MC but answer missing in source
 */
function uiType(q) {
  if (q.type === 'hotspot') {
    // Detect ordering first — even when the answer is absent — so the correct
    // interaction UI is shown regardless of whether grading data is available.
    const sub = q.hotspot_subtype ?? '';
    if (sub === 'ordering' || /select\s+and\s+order/i.test(q.question)) return 'hs-ordering';
    if (sub === 'multi-slot' || /more than one time/i.test(q.question))  return 'hs-multi-slot';
    if (!q.answer || (Array.isArray(q.answer) && !q.answer.length)) return 'hs-noanswer';
    if (Array.isArray(q.answer) && typeof q.answer[0] === 'object')  return 'hs-matching';
    return 'hs-selection';
  }
  if (!q.answer) return 'mc-noanswer';
  if (Array.isArray(q.answer)) return 'mc-multiple';
  return 'mc-single';
}

// ── API ───────────────────────────────────────────────────────────────────────

async function apiFetch(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`Server returned ${r.status}`);
  return r.json();
}

// ── HOME SCREEN ───────────────────────────────────────────────────────────────

async function initHome() {
  showScreen('home');
  el('exam-list').innerHTML = '<p class="text-gray-400 text-center py-8">Loading…</p>';
  try {
    state.exams = await apiFetch('/api/exams');
    renderExamList();
  } catch(e) {
    el('exam-list').innerHTML =
      `<p class="text-red-500 text-center py-8">Could not load exams: ${esc(e.message)}</p>`;
  }
}

function renderExamList() {
  if (!state.exams.length) {
    el('exam-list').innerHTML =
      '<p class="text-gray-400 text-center py-8">No .json exam files found in the data directory.</p>';
    return;
  }
  el('exam-list').innerHTML = state.exams.map((exam, i) => `
    <div class="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm
                flex items-center justify-between gap-4 hover:shadow-md transition-shadow">
      <div>
        <h2 class="font-semibold text-gray-900 text-lg leading-tight">${esc(exam.name)}</h2>
        <p class="text-sm text-gray-400 mt-1">${esc(exam.code)} · ${exam.total_questions} questions</p>
      </div>
      <button onclick="App.selectExam(${i})"
        class="flex-shrink-0 bg-blue-600 hover:bg-blue-700 text-white font-medium
               px-5 py-2.5 rounded-xl transition-colors text-sm">
        Start →
      </button>
    </div>
  `).join('');
}

// ── SETUP SCREEN ─────────────────────────────────────────────────────────────

function selectExam(idx) {
  state.selectedExam = state.exams[idx];
  const max = state.selectedExam.total_questions;
  el('setup-title').textContent = state.selectedExam.name;
  el('setup-code').textContent  = state.selectedExam.code;
  const slider = el('setup-count');
  slider.max   = max;
  slider.value = Math.min(10, max);
  el('count-max').textContent     = max;
  el('count-display').textContent = slider.value;
  showScreen('setup');
}

function initSetupEvents() {
  el('setup-count').addEventListener('input', () => {
    el('count-display').textContent = el('setup-count').value;
  });
  el('btn-start').addEventListener('click', startSession);
  el('btn-next').addEventListener('click', handleNext);
  el('btn-continue').addEventListener('click', handleContinue);
  el('btn-retry').addEventListener('click', retryIncorrect);
  el('btn-new-session').addEventListener('click', () => App.goHome());
}

async function startSession() {
  const count      = parseInt(el('setup-count').value, 10);
  const randomize  = el('setup-random').checked;

  el('btn-start').disabled = true;
  el('btn-start').textContent = 'Loading…';
  try {
    const data = await apiFetch(`/api/exam/${encodeURIComponent(state.selectedExam.filename)}`);
    state.allQuestions = data.questions ?? [];
  } catch(e) {
    alert('Failed to load exam: ' + e.message);
    el('btn-start').disabled = false;
    el('btn-start').textContent = 'Start Exam →';
    return;
  }
  el('btn-start').disabled = false;
  el('btn-start').textContent = 'Start Exam →';

  beginSession(state.allQuestions, count, randomize);
}

function beginSession(pool, count, randomize) {
  let questions = [...pool];
  if (randomize) shuffle(questions);          // random: draw from whole shuffled pool
  state.sessionQuestions = questions.slice(0, count);
  shuffle(state.sessionQuestions);             // always vary the order within the selection
  state.currentIdx       = 0;
  state.results          = [];
  state.retryMode        = false;
  showScreen('question');
  renderQuestion();
}

function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
}

// ── QUESTION SCREEN ───────────────────────────────────────────────────────────

function renderQuestion() {
  const q     = state.sessionQuestions[state.currentIdx];
  const num   = state.currentIdx + 1;
  const total = state.sessionQuestions.length;
  const pct   = Math.round((num / total) * 100);
  const type  = uiType(q);

  // Progress
  el('q-num').textContent          = `Question ${num} of ${total}`;
  el('q-progress').style.width     = `${pct}%`;
  el('q-progress-text').textContent = `${pct}%`;

  // Type badge
  const badge     = el('q-type-badge');
  badge.textContent = badgeLabel(type);
  badge.className   = `inline-block px-3 py-1 rounded-full text-xs font-semibold ${badgeClass(type)}`;

  // PDF question number + back-button visibility
  const numBtn = el('q-actual-num');
  numBtn.dataset.qnum = `Q${q.question_number}`;
  numBtn.textContent   = 'Q•••';
  numBtn.dataset.revealed = 'false';
  el('btn-prev').classList.toggle('hidden', state.currentIdx === 0);

  // Question text
  el('q-text').textContent = q.question;

  // Input area
  state._ordering = [];
  el('q-inputs').innerHTML = buildInputs(q, type);
}

function badgeLabel(t) {
  return {
    'mc-single':    'Single Choice',
    'mc-multiple':  'Multiple Choice',
    'mc-noanswer':  'Single Choice',
    'hs-selection':  'Multi-Select',
    'hs-ordering':   'Ordering',
    'hs-matching':   'Dropdown',
    'hs-multi-slot': 'Multi-Slot',
    'hs-noanswer':   'Multi-Select',
  }[t] ?? 'Question';
}

function badgeClass(t) {
  if (t === 'mc-single' || t === 'mc-noanswer') return 'bg-blue-100 text-blue-700';
  if (t === 'mc-multiple')   return 'bg-purple-100 text-purple-700';
  if (t === 'hs-matching')   return 'bg-amber-100 text-amber-700';
  if (t === 'hs-ordering')   return 'bg-green-100 text-green-700';
  if (t === 'hs-multi-slot') return 'bg-orange-100 text-orange-700';
  return 'bg-teal-100 text-teal-700';
}

// ── INPUT BUILDERS ────────────────────────────────────────────────────────────

function buildInputs(q, type) {
  switch (type) {
    case 'mc-single':
    case 'mc-noanswer':
      return buildMCSingle(q);
    case 'mc-multiple':
      return buildMCMultiple(q);
    case 'hs-selection':
    case 'hs-noanswer':
      return buildHSSelection(q);
    case 'hs-ordering':
      return buildHSOrdering(q);
    case 'hs-matching':
      return buildHSMatching(q);
    case 'hs-multi-slot':
      return buildHSMultiSlot(q);
    default:
      return buildMCSingle(q);
  }
}

function buildMCSingle(q) {
  const entries = Object.entries(q.options ?? {});
  shuffle(entries);
  return entries.map(([k, v]) => `
    <label class="opt-label flex items-start gap-3 p-4 rounded-xl border-2 border-gray-200
                  cursor-pointer hover:border-blue-300 hover:bg-blue-50 transition-all">
      <input type="radio" name="mc" value="${esc(k)}"
        class="mt-0.5 w-4 h-4 accent-blue-600 flex-shrink-0 cursor-pointer">
      <span><b class="text-blue-600">${esc(k)}.</b> ${esc(v)}</span>
    </label>
  `).join('');
}

function buildMCMultiple(q) {
  const count   = Array.isArray(q.answer) ? q.answer.length : '?';
  const entries = Object.entries(q.options ?? {});
  shuffle(entries);
  return `<p class="text-xs text-gray-400 mb-2">Choose ${count} answer(s)</p>` +
    entries.map(([k, v]) => `
      <label class="opt-label flex items-start gap-3 p-4 rounded-xl border-2 border-gray-200
                    cursor-pointer hover:border-purple-300 hover:bg-purple-50 transition-all">
        <input type="checkbox" name="mc" value="${esc(k)}"
          class="mt-0.5 w-4 h-4 accent-purple-600 flex-shrink-0 cursor-pointer">
        <span><b class="text-purple-600">${esc(k)}.</b> ${esc(v)}</span>
      </label>
    `).join('');
}

function buildHSSelection(q) {
  const opts  = [...(q.options ?? [])];
  shuffle(opts);
  if (!opts.length) return '<p class="text-gray-400 italic">No options available.</p>';
  const count = Array.isArray(q.answer) && q.answer.length ? q.answer.length : null;
  const hint  = count ? `Select ${count} correct answer(s)` : 'Select all that apply';
  return `<p class="text-xs text-gray-400 mb-2">${hint}</p>` +
    opts.map((opt, i) => `
      <label class="opt-label-teal flex items-start gap-3 p-4 rounded-xl border-2 border-gray-200
                    cursor-pointer hover:border-teal-300 hover:bg-teal-50 transition-all">
        <input type="checkbox" name="hs" value="${i}"
          data-opt="${esc(opt)}"
          class="mt-0.5 w-4 h-4 accent-teal-600 flex-shrink-0 cursor-pointer">
        <span>${esc(opt)}</span>
      </label>
    `).join('');
}

function buildHSOrdering(q) {
  const opts = [...(q.options ?? [])];
  shuffle(opts);
  if (!opts.length) return '<p class="text-gray-400 italic">No options available.</p>';
  return `<p class="text-xs text-gray-400 mb-2">Click items in the correct order. Click again to deselect.</p>
    <div class="flex flex-col gap-2">
      ${opts.map((opt, i) => `
        <button type="button" id="order-btn-${i}"
          data-idx="${i}" data-val="${esc(opt)}"
          onclick="App.toggleOrder(this)"
          class="order-btn text-left flex items-center gap-3 px-4 py-3 rounded-xl
                 border-2 border-gray-200 hover:border-green-300 hover:bg-green-50 transition-all">
          <span id="order-badge-${i}"
            class="w-7 h-7 rounded-full border-2 border-gray-300 flex items-center justify-center
                   text-xs font-bold text-gray-400 flex-shrink-0"></span>
          <span>${esc(opt)}</span>
        </button>
      `).join('')}
    </div>`;
}

function buildHSMatching(q) {
  const opts  = q.options ?? [];
  const pairs = Array.isArray(q.answer) ? q.answer : [];
  if (!pairs.length) return '<p class="text-gray-400 italic">No matching pairs available.</p>';
  return `<p class="text-xs text-gray-400 mb-3">Select the correct answer from each dropdown.</p>
    <div class="flex flex-col gap-3">
      ${pairs.map((pair, i) => `
        <div class="flex flex-col sm:flex-row sm:items-center gap-2
                    p-4 bg-gray-50 rounded-xl border-2 border-gray-200">
          <span class="flex-1 text-sm font-medium text-gray-800">${esc(pair.statement)}</span>
          <select name="match" data-stmt="${esc(pair.statement)}"
            class="sm:w-56 border-2 border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700
                   focus:border-amber-400 focus:outline-none bg-white cursor-pointer">
            <option value="">— Select —</option>
            ${opts.map(opt => `<option value="${esc(opt)}">${esc(opt)}</option>`).join('')}
          </select>
        </div>
      `).join('')}
    </div>`;
}

function buildHSMultiSlot(q) {
  const opts = q.options ?? [];
  if (!opts.length) return '<p class="text-gray-400 italic">No options available.</p>';
  // Determine slot count from answer length, falling back to "(Choose N)" in the question.
  let slots = Array.isArray(q.answer) ? q.answer.length : 0;
  if (!slots) {
    const m = q.question.match(/\(Choose\s+(\w+)\.?\)/i);
    if (m) {
      const words = {one:1,two:2,three:3,four:4,five:5,six:6,seven:7,eight:8,nine:9,ten:10};
      slots = words[m[1].toLowerCase()] ?? parseInt(m[1], 10) || opts.length;
    } else {
      slots = opts.length;
    }
  }
  return `<p class="text-xs text-gray-400 mb-3">Select one option per slot. The same option may be used more than once.</p>
    <div class="flex flex-col gap-3">
      ${Array.from({length: slots}, (_, i) => `
        <div class="flex flex-col sm:flex-row sm:items-center gap-2
                    p-4 bg-gray-50 rounded-xl border-2 border-gray-200">
          <span class="flex-shrink-0 w-16 text-sm font-semibold text-orange-600">Slot ${i + 1}</span>
          <select name="multi-slot" data-slot="${i}"
            class="flex-1 border-2 border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700
                   focus:border-orange-400 focus:outline-none bg-white cursor-pointer">
            <option value="">— Select —</option>
            ${opts.map(opt => `<option value="${esc(opt)}">${esc(opt)}</option>`).join('')}
          </select>
        </div>
      `).join('')}
    </div>`;
}

// ── Ordering toggle (called from inline onclick) ───────────────────────────────

function toggleOrder(btn) {
  const idx = parseInt(btn.dataset.idx, 10);
  const val = btn.dataset.val;
  const pos = state._ordering.findIndex(o => o.idx === idx);

  if (pos !== -1) {
    state._ordering.splice(pos, 1);
  } else {
    state._ordering.push({ idx, val });
  }
  refreshOrderBadges();
}

function refreshOrderBadges() {
  document.querySelectorAll('.order-btn').forEach(btn => {
    const idx   = parseInt(btn.dataset.idx, 10);
    const badge = el(`order-badge-${idx}`);
    const pos   = state._ordering.findIndex(o => o.idx === idx);

    if (pos !== -1) {
      badge.textContent  = pos + 1;
      badge.className = badge.className
        .replace('border-gray-300 text-gray-400', 'border-green-500 bg-green-500 text-white');
      btn.classList.add('selected');
    } else {
      badge.textContent = '';
      badge.className = badge.className
        .replace('border-green-500 bg-green-500 text-white', 'border-gray-300 text-gray-400');
      btn.classList.remove('selected');
    }
  });
}

// ── ANSWER COLLECTION ─────────────────────────────────────────────────────────

function collectAnswer() {
  const q    = state.sessionQuestions[state.currentIdx];
  const type = uiType(q);

  switch (type) {
    case 'mc-single':
    case 'mc-noanswer': {
      const sel = document.querySelector('input[name="mc"]:checked');
      return sel ? sel.value : null;
    }
    case 'mc-multiple': {
      const checked = [...document.querySelectorAll('input[name="mc"]:checked')];
      return checked.length ? checked.map(c => c.value) : null;
    }
    case 'hs-selection':
    case 'hs-noanswer': {
      const checked = [...document.querySelectorAll('input[name="hs"]:checked')];
      return checked.length ? checked.map(c => c.dataset.opt) : null;
    }
    case 'hs-ordering':
      return state._ordering.length ? state._ordering.map(o => o.val) : null;
    case 'hs-multi-slot': {
      const selects = [...document.querySelectorAll('select[name="multi-slot"]')];
      if (selects.some(s => !s.value)) return null;   // some slots unfilled
      return selects.map(s => s.value);
    }
    case 'hs-matching': {
      const selects = [...document.querySelectorAll('select[name="match"]')];
      if (selects.some(s => !s.value)) return null;   // some dropdowns unfilled
      const result = {};
      selects.forEach(s => { result[s.dataset.stmt] = s.value; });
      return result;
    }
    default: return null;
  }
}

// ── ANSWER CHECKING ───────────────────────────────────────────────────────────

/** Returns true/false, or null when the correct answer is unknown. */
function checkAnswer(userAnswer, q) {
  if (!q.answer)          return null;   // source has no answer
  if (userAnswer === null) return false;  // skipped

  const type = uiType(q);

  switch (type) {
    case 'mc-single':
    case 'mc-noanswer':
      return norm(userAnswer) === norm(q.answer);

    case 'mc-multiple': {
      if (!Array.isArray(userAnswer)) return false;
      const a = [...q.answer].map(norm).sort();
      const b = [...userAnswer].map(norm).sort();
      return JSON.stringify(a) === JSON.stringify(b);
    }

    case 'hs-selection': {
      if (!Array.isArray(userAnswer) || !Array.isArray(q.answer)) return false;
      const a = q.answer.map(norm).sort();
      const b = userAnswer.map(norm).sort();
      return JSON.stringify(a) === JSON.stringify(b);
    }

    case 'hs-ordering': {
      if (!q.answer) return null;   // answer not in source — cannot grade
      if (!Array.isArray(userAnswer) || !Array.isArray(q.answer)) return false;
      if (userAnswer.length !== q.answer.length) return false;
      return q.answer.every((item, i) => norm(item) === norm(userAnswer[i]));
    }

    case 'hs-multi-slot': {
      if (!Array.isArray(userAnswer) || !Array.isArray(q.answer)) return false;
      // Order within slots is unknown, so compare sorted counts.
      const a = [...q.answer].map(norm).sort();
      const b = [...userAnswer].map(norm).sort();
      return JSON.stringify(a) === JSON.stringify(b);
    }

    case 'hs-matching': {
      if (!userAnswer || !Array.isArray(q.answer)) return false;
      return q.answer.every(pair => {
        const sel = userAnswer[pair.statement];
        return sel && norm(sel) === norm(pair.answer);
      });
    }

    default: return null;
  }
}

// ── NEXT BUTTON ───────────────────────────────────────────────────────────────

function handleNext() {
  const q          = state.sessionQuestions[state.currentIdx];
  const userAnswer = collectAnswer();
  const skipped    = userAnswer === null;
  const verdict    = skipped ? false : checkAnswer(userAnswer, q);

  state.results.push({
    question:   q,
    userAnswer: skipped ? null : userAnswer,
    skipped,
    isCorrect:  verdict === null ? false : verdict,
    hasAnswer:  q.answer != null,
  });

  showFeedback(state.results.at(-1));
}

// ── FEEDBACK SCREEN ───────────────────────────────────────────────────────────

function showFeedback(result) {
  showScreen('feedback');
  const { question: q, userAnswer, isCorrect, skipped, hasAnswer } = result;
  const num   = state.currentIdx + 1;
  const total = state.sessionQuestions.length;
  const type  = uiType(q);

  el('fb-num').textContent      = `Question ${num} of ${total}`;
  el('fb-actual-num').textContent = `Q${q.question_number}`;

  // Status banner
  let statusHtml;
  if (!hasAnswer) {
    statusHtml = `<span class="text-amber-500">⚠️ Correct answer not available in source</span>`;
  } else if (isCorrect) {
    statusHtml = `<span class="text-green-600">✅ Correct!</span>`;
  } else if (skipped) {
    statusHtml = `<span class="text-red-500">❌ Skipped — marked as incorrect</span>`;
  } else {
    statusHtml = `<span class="text-red-500">❌ Incorrect</span>`;
  }
  el('fb-status').innerHTML = statusHtml;

  el('fb-question').textContent = q.question;

  // All choices (colour-coded)
  el('fb-all-choices').innerHTML = renderAllChoices(userAnswer, q, type, hasAnswer);

  // Matching detail table
  if (type === 'hs-matching' && hasAnswer && !skipped) {
    el('fb-match-table').classList.remove('hidden');
    el('fb-match-rows').innerHTML = buildMatchTable(userAnswer, q.answer);
  } else {
    el('fb-match-table').classList.add('hidden');
  }

  // Explanation
  const expDiv = el('fb-explanation');
  if (q.explanation) {
    expDiv.classList.remove('hidden');
    expDiv.querySelector('.explanation-box').textContent = q.explanation;
  } else {
    expDiv.classList.add('hidden');
  }

  const isLast = num >= total;
  el('btn-continue').textContent = isLast ? 'See Results →' : 'Continue →';
}

function formatAnswer(answer, q, type, mode, isCorrect) {
  if (answer === null || answer === undefined) {
    return mode === 'user'
      ? '<span class="text-gray-400 italic">No answer selected</span>'
      : '<span class="text-gray-400 italic">Not available</span>';
  }

  const opts = q.options ?? {};

  if (type === 'mc-single' || type === 'mc-noanswer') {
    const letter = String(answer);
    const text   = opts[letter] ?? '';
    return `<span class="font-semibold text-blue-700">${esc(letter)}.</span> ${esc(text)}`;
  }

  if (type === 'mc-multiple') {
    const letters = Array.isArray(answer) ? answer : [answer];
    return letters.map(l =>
      `<div><span class="font-semibold text-purple-700">${esc(l)}.</span> ${esc(opts[l] ?? '')}</div>`
    ).join('');
  }

  if (type === 'hs-selection' || type === 'hs-noanswer') {
    const items = Array.isArray(answer) ? answer : [answer];
    return items.map(item =>
      `<div class="flex gap-2"><span class="text-teal-500">•</span><span>${esc(item)}</span></div>`
    ).join('');
  }

  if (type === 'hs-multi-slot') {
    const items = Array.isArray(answer) ? answer : [answer];
    return items.map((item, i) =>
      `<div class="flex gap-2"><span class="text-orange-500 font-semibold min-w-[3.5rem]">Slot ${i+1}</span><span>${esc(item)}</span></div>`
    ).join('');
  }

  if (type === 'hs-ordering') {
    const items = Array.isArray(answer) ? answer : [answer];
    return items.map((item, i) =>
      `<div class="flex gap-2"><span class="font-bold text-green-600 min-w-[1.2rem]">${i+1}.</span><span>${esc(item)}</span></div>`
    ).join('');
  }

  if (type === 'hs-matching') {
    if (Array.isArray(answer)) {
      // Correct answer array of {statement, answer}
      return answer.map(p =>
        `<div class="py-0.5"><span class="text-gray-500 text-xs">${esc(p.statement)}</span>
         <div class="font-semibold text-amber-700">${esc(p.answer)}</div></div>`
      ).join('<hr class="my-1 border-gray-100">');
    }
    if (typeof answer === 'object') {
      // User answer object {statement: value}
      return Object.entries(answer).map(([stmt, val]) =>
        `<div class="py-0.5"><span class="text-gray-500 text-xs">${esc(stmt)}</span>
         <div class="font-semibold text-amber-700">${esc(val)}</div></div>`
      ).join('<hr class="my-1 border-gray-100">');
    }
  }

  return `<span>${esc(String(answer))}</span>`;
}

function buildMatchTable(userAnswer, correctPairs) {
  return correctPairs.map(pair => {
    const userVal  = (userAnswer ?? {})[pair.statement] ?? '';
    const ok       = norm(userVal) === norm(pair.answer);
    const rowBg    = ok ? 'bg-green-50' : 'bg-red-50';
    return `
      <tr class="${rowBg}">
        <td class="px-3 py-2 text-xs text-gray-700 align-top max-w-[180px]">${esc(pair.statement)}</td>
        <td class="px-3 py-2 text-xs align-top ${ok ? 'text-green-700':'text-red-600'}">${esc(userVal) || '—'}</td>
        <td class="px-3 py-2 text-xs align-top text-green-700 font-medium">${esc(pair.answer)}</td>
        <td class="px-3 py-2 text-center text-sm">${ok ? '✅' : '❌'}</td>
      </tr>`;
  }).join('');
}

// ── CONTINUE BUTTON ───────────────────────────────────────────────────────────

function handleContinue() {
  state.currentIdx++;
  if (state.currentIdx >= state.sessionQuestions.length) {
    showSummary();
  } else {
    showScreen('question');
    renderQuestion();
  }
}

// ── SUMMARY SCREEN ────────────────────────────────────────────────────────────

function showSummary() {
  showScreen('summary');
  const results   = state.results;
  const total     = results.length;
  const correct   = results.filter(r => r.isCorrect).length;
  const incorrect = total - correct;
  const pct       = total ? Math.round((correct / total) * 100) : 0;

  el('sum-mode-label').textContent = state.retryMode ? 'Retry Complete!' : 'Exam Complete!';
  el('sum-exam-name').textContent  = state.selectedExam?.name ?? '';
  el('sum-total').textContent      = total;
  el('sum-correct').textContent    = correct;
  el('sum-incorrect').textContent  = incorrect;
  el('sum-score').textContent      = `${pct}%`;

  // Colour the score ring
  const ring = el('sum-score-ring');
  ring.className = 'score-ring ' + (
    pct >= 80 ? 'text-green-500' :
    pct >= 60 ? 'text-yellow-500' : 'text-red-500'
  );

  // Retry button
  const badResults = results.filter(r => !r.isCorrect);
  if (badResults.length) {
    el('btn-retry').classList.remove('hidden');
    el('btn-retry').textContent = `Retry ${badResults.length} Incorrect →`;
  } else {
    el('btn-retry').classList.add('hidden');
  }
}

function retryIncorrect() {
  const bad = state.results.filter(r => !r.isCorrect).map(r => r.question);
  state.retryMode        = true;
  state.currentIdx       = 0;
  state.results          = [];
  state.sessionQuestions = bad;
  showScreen('question');
  renderQuestion();
}

// ── BACK / SETUP NAVIGATION ───────────────────────────────────────────────────

function handleRevise() {
  state.results.pop();   // remove the just-submitted result
  showScreen('question');
  renderQuestion();      // re-render the same question (currentIdx unchanged)
}

function handleBack() {
  if (state.currentIdx === 0) return;
  state.results.pop();
  state.currentIdx--;
  showScreen('question');
  renderQuestion();
}

function goToSetup() {
  if (!state.results.length || confirm('Return to setup? Your progress will be lost.')) {
    showScreen('setup');
  }
}

// ── ALL CHOICES RENDERER ──────────────────────────────────────────────────────

function renderAllChoices(userAnswer, q, type, hasAnswer) {
  // MC single / multiple
  if (['mc-single', 'mc-multiple', 'mc-noanswer'].includes(type)) {
    const mcOpts     = q.options ?? {};
    const correctSet = new Set(
      Array.isArray(q.answer) ? q.answer.map(norm)
        : (q.answer ? [norm(q.answer)] : [])
    );
    const userSet = new Set(
      userAnswer === null ? []
        : Array.isArray(userAnswer) ? userAnswer.map(norm)
        : [norm(userAnswer)]
    );
    return '<div class="flex flex-col gap-2">' +
      Object.entries(mcOpts).map(([k, v]) => {
        const isRight = hasAnswer && correctSet.has(norm(k));
        const isUser  = userSet.has(norm(k));
        let bg    = 'bg-gray-50 border-gray-200';
        let badge = '';
        if (isRight && isUser)         { bg = 'bg-green-50 border-green-300'; badge = '<span class="text-green-600 text-sm font-medium whitespace-nowrap">✅ Your answer</span>'; }
        else if (isRight)              { bg = 'bg-green-50 border-green-300'; badge = '<span class="text-green-600 text-sm font-medium">✅ Correct</span>'; }
        else if (isUser)               { bg = 'bg-red-50 border-red-300';     badge = '<span class="text-red-500 text-sm font-medium whitespace-nowrap">❌ Your answer</span>'; }
        else if (!hasAnswer && isUser) { bg = 'bg-blue-50 border-blue-200';   badge = '<span class="text-blue-500 text-sm font-medium whitespace-nowrap">Your answer</span>'; }
        return `<div class="flex items-start gap-3 p-3 rounded-xl border ${bg}">` +
          `<span class="font-bold min-w-[1.4rem] flex-shrink-0 mt-0.5">${esc(k)}.</span>` +
          `<span class="flex-1 text-sm text-gray-700">${esc(v)}</span>` +
          `<div class="flex-shrink-0 ml-2">${badge}</div></div>`;
      }).join('') + '</div>';
  }

  // HOTSPOT selection
  if (['hs-selection', 'hs-noanswer'].includes(type)) {
    const hsOpts     = Array.isArray(q.options) ? q.options : [];
    const correctSet = new Set(Array.isArray(q.answer) ? q.answer.map(norm) : []);
    const userSet    = new Set(
      userAnswer === null ? []
        : Array.isArray(userAnswer) ? userAnswer.map(norm)
        : [norm(userAnswer)]
    );
    return '<div class="flex flex-col gap-2">' +
      hsOpts.map(opt => {
        const isRight = hasAnswer && correctSet.has(norm(opt));
        const isUser  = userSet.has(norm(opt));
        let bg    = 'bg-gray-50 border-gray-200';
        let badge = '';
        if (isRight && isUser)         { bg = 'bg-green-50 border-green-300'; badge = '<span class="text-green-600 text-sm font-medium whitespace-nowrap">✅ Your answer</span>'; }
        else if (isRight)              { bg = 'bg-green-50 border-green-300'; badge = '<span class="text-green-600 text-sm font-medium">✅ Correct</span>'; }
        else if (isUser)               { bg = 'bg-red-50 border-red-300';     badge = '<span class="text-red-500 text-sm font-medium whitespace-nowrap">❌ Your answer</span>'; }
        else if (!hasAnswer && isUser) { bg = 'bg-blue-50 border-blue-200';   badge = '<span class="text-blue-500 text-sm font-medium whitespace-nowrap">Your answer</span>'; }
        return `<div class="flex items-start gap-3 p-3 rounded-xl border ${bg}">` +
          `<span class="flex-1 text-sm text-gray-700">${esc(opt)}</span>` +
          `<div class="flex-shrink-0 ml-2">${badge}</div></div>`;
      }).join('') + '</div>';
  }

  // HOTSPOT ordering
  if (type === 'hs-ordering') {
    const hsOpts     = Array.isArray(q.options) ? q.options : [];
    const correctArr = Array.isArray(q.answer) ? q.answer : [];
    const userArr    = userAnswer === null ? [] : (Array.isArray(userAnswer) ? userAnswer : []);
    return '<div class="flex flex-col gap-2">' +
      hsOpts.map(opt => {
        const cIdx  = correctArr.findIndex(a => norm(a) === norm(opt));
        const uIdx  = userArr.findIndex(a => norm(a) === norm(opt));
        const inC   = cIdx !== -1;
        const inU   = uIdx !== -1;
        const match = inC && inU && cIdx === uIdx;
        let bg       = 'bg-gray-50 border-gray-200';
        let badge    = '';
        let posLabel = `<span class="min-w-[1.5rem] flex-shrink-0 text-gray-300 font-bold">—</span>`;
        if (inC && inU) {
          bg       = match ? 'bg-green-50 border-green-300' : 'bg-yellow-50 border-yellow-300';
          posLabel = `<span class="min-w-[1.5rem] flex-shrink-0 font-bold text-green-700">${cIdx+1}.</span>`;
          badge    = match
            ? `<span class="text-green-600 text-sm font-medium whitespace-nowrap">✅ #${cIdx+1}</span>`
            : `<span class="text-yellow-600 text-sm font-medium whitespace-nowrap">⚠️ Correct #${cIdx+1} · Yours #${uIdx+1}</span>`;
        } else if (inC) {
          bg       = 'bg-green-50 border-green-300';
          posLabel = `<span class="min-w-[1.5rem] flex-shrink-0 font-bold text-green-700">${cIdx+1}.</span>`;
          badge    = `<span class="text-green-600 text-sm font-medium whitespace-nowrap">✅ Correct #${cIdx+1} (missed)</span>`;
        } else if (inU) {
          bg    = 'bg-red-50 border-red-300';
          badge = `<span class="text-red-500 text-sm font-medium whitespace-nowrap">❌ Your #${uIdx+1} (wrong item)</span>`;
        }
        return `<div class="flex items-center gap-3 p-3 rounded-xl border ${bg}">` +
          posLabel +
          `<span class="flex-1 text-sm text-gray-700">${esc(opt)}</span>` +
          `<div class="flex-shrink-0 ml-2">${badge}</div></div>`;
      }).join('') + '</div>';
  }

  // Multi-slot: show per-slot comparison
  if (type === 'hs-multi-slot') {
    const hsOpts   = Array.isArray(q.options) ? q.options : [];
    const correctArr = Array.isArray(q.answer) ? [...q.answer].map(norm).sort() : [];
    const userArr    = userAnswer === null ? [] : (Array.isArray(userAnswer) ? [...userAnswer].map(norm).sort() : []);
    // Count occurrences in correct vs user answers
    return '<div class="flex flex-col gap-2">' +
      hsOpts.map(opt => {
        const nopt    = norm(opt);
        const cCount  = correctArr.filter(v => v === nopt).length;
        const uCount  = userArr.filter(v => v === nopt).length;
        const match   = hasAnswer && cCount === uCount;
        const bg      = !hasAnswer ? 'bg-gray-50 border-gray-200'
                      : match     ? 'bg-green-50 border-green-300'
                                  : (cCount > 0 || uCount > 0) ? 'bg-red-50 border-red-300'
                                  : 'bg-gray-50 border-gray-200';
        let badge = '';
        if (hasAnswer && cCount > 0 && uCount > 0 && match)
          badge = `<span class="text-green-600 text-sm font-medium whitespace-nowrap">✅ ×${cCount}</span>`;
        else if (hasAnswer && cCount > 0 && uCount === 0)
          badge = `<span class="text-green-600 text-sm font-medium whitespace-nowrap">✅ Expected ×${cCount}</span>`;
        else if (hasAnswer && uCount > 0 && cCount === 0)
          badge = `<span class="text-red-500 text-sm font-medium whitespace-nowrap">❌ Yours ×${uCount}</span>`;
        else if (hasAnswer && cCount !== uCount)
          badge = `<span class="text-red-500 text-sm font-medium whitespace-nowrap">❌ Need ×${cCount}, got ×${uCount}</span>`;
        else if (!hasAnswer && uCount > 0)
          badge = `<span class="text-blue-500 text-sm font-medium whitespace-nowrap">Yours ×${uCount}</span>`;
        return `<div class="flex items-center gap-3 p-3 rounded-xl border ${bg}">` +
          `<span class="flex-1 text-sm text-gray-700">${esc(opt)}</span>` +
          `<div class="flex-shrink-0 ml-2">${badge}</div></div>`;
      }).join('') + '</div>';
  }

  // Matching: handled by fb-match-table
  return '';
}

// ── PUBLIC API (called from HTML inline handlers) ─────────────────────────────

const App = {
  selectExam,
  toggleOrder,
  goHome:       () => initHome(),
  goToSetup,
  handleBack,
  handleRevise,
};

// ── INIT ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  initSetupEvents();
  // Click-to-toggle question number visibility
  el('q-actual-num').addEventListener('click', () => {
    const btn = el('q-actual-num');
    const revealed = btn.dataset.revealed === 'true';
    if (revealed) {
      btn.textContent      = 'Q\u2022\u2022\u2022';
      btn.dataset.revealed = 'false';
      btn.title            = 'Click to reveal question number';
      btn.classList.replace('tracking-normal', 'tracking-widest');
    } else {
      btn.textContent      = btn.dataset.qnum;
      btn.dataset.revealed = 'true';
      btn.title            = 'Click to hide question number';
      btn.classList.replace('tracking-widest', 'tracking-normal');
    }
  });
  initHome();
});
