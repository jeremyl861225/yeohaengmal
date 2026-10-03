// 文法專欄（2026-10-03）：27 課，從語序、助詞到旅行最常用的句型；內容在 data/grammar.json（tools/build_grammar.py 產生）。
// 畫面：課程表（#/grammar）、一課（#/grammar/<id>：重點、變化表、例句點了就聽、小提醒）、練習（#/grammar/<id>/practice）。
// 練習三種題型：填空（選助詞或語尾）、選出正確的句子、聽句子選意思；成績存在 store.grammar，八成以上算學完。
// 結構照 letters.js：app.js 用 setupGrammar(ctx) 把共用的東西傳進來。

let C = null;
let G = null;
let loading = null;
let prac = null;

export function setupGrammar(ctx) { C = ctx; }

export function loadGrammar() {
  if (G) return Promise.resolve(G);
  if (!loading) loading = fetch('data/grammar.json').then((r) => r.json()).then((d) => { G = d; return d; });
  return loading;
}

const lessons = () => G.groups.flatMap((g) => g.lessons);
const rec = (id) => (C.store.grammar || {})[id] || {};
const url = (key) => `audio/${key}.mp3`;
const plain = (ko) => ko.replace(/[[\]]/g, '');

// 設定頁「離線使用」整批下載：例句與練習題的音檔
export function grammarAudio() {
  if (!G) return [];
  const keys = new Set();
  lessons().forEach((l) => { l.ex.forEach((e) => keys.add(e.a)); l.quiz.forEach((q) => keys.add(q.au)); });
  return [...keys].map(url);
}

// 首頁入口格用：學完幾課／共幾課
export function grammarProgress() {
  if (!G) return null;
  const all = lessons();
  return { done: all.filter((l) => rec(l.id).done).length, total: all.length, next: all.find((l) => !rec(l.id).done) || null };
}

// 說明文字：**粗體**，韓文字轉成 lang="ko"（才會用韓文明朝體）
function rich(s) {
  return C.esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/[가-힣ㄱ-ㅣ]+/g, '<span lang="ko">$&</span>');
}
// 例句：[ ] 框起來的是這課的重點
const hl = (ko) => C.esc(ko).replace(/\[([^\]]+)\]/g, '<em>$1</em>');
const speaker = (key, cls = 'd-say') => `<button class="${cls}" data-gm-say="${key}" aria-label="播放">${C.I.speaker('ico-s')}</button>`;

function whenReady(fn) {
  if (G) return fn();
  C.$app.innerHTML = `<p class="none">載入中…</p>`;
  loadGrammar().then(fn).catch(() => C.toast('文法資料載入失敗，連上網路後再試一次'));
}

/* ---------- 課程表 ---------- */
export function viewGrammar() {
  whenReady(() => {
    const all = lessons();
    const next = all.find((l) => !rec(l.id).done);
    let n = 0;
    const groups = G.groups.map((g) => `
      <h2 class="group-title">${C.esc(g.title)}</h2>
      <div class="list lt-list">${g.lessons.map((l) => {
        n += 1;
        const r = rec(l.id);
        const state = r.done ? `<span class="lt-done">${C.I.check('ico-s')}學完</span>` : l === next ? '<span class="lt-next">下一課</span>' : '';
        return `<a class="row lt-row${l === next ? ' cur' : ''}" href="#/grammar/${l.id}">
          <span class="lt-n">${n}</span>
          <span class="r-main"><span class="lt-title" data-fit="14">${rich(l.title)}</span><span class="lt-sub" data-fit="11">${rich(l.sub)}${r.best != null ? `　練習 ${r.best}/${r.total}` : ''}</span></span>
          ${state}
        </a>`;
      }).join('')}</div>`).join('');
    C.$app.innerHTML = `
      <div class="topbar"><a class="icon-btn" href="#/" aria-label="回路線圖">${C.I.back()}</a><span class="title">${C.esc(G.title)}</span></div>
      <header class="lt-head"><h1 data-fit="22">${C.esc(G.title)}</h1><p>${C.esc(G.intro)}</p></header>
      <div class="lt-actions">
        ${next ? `<a class="pill" href="#/grammar/${next.id}">${all.some((l) => rec(l.id).best != null) ? '繼續' : '開始'}：${rich(next.title)}</a>` : ''}
      </div>
      ${groups}`;
  });
}

/* ---------- 一課 ---------- */
function tableHTML(t) {
  return `<div class="panel gm-table${t.head.length >= 4 ? ' c4' : ''}"><table>
    <thead><tr>${t.head.map((h) => `<th>${rich(h)}</th>`).join('')}</tr></thead>
    <tbody>${t.rows.map((r) => `<tr>${r.map((c) => `<td>${rich(c)}</td>`).join('')}</tr>`).join('')}</tbody>
  </table></div>`;
}

export function viewGrammarLesson(id) {
  whenReady(() => {
    const all = lessons();
    const i = all.findIndex((l) => l.id === id);
    if (i < 0) return location.replace('#/grammar');
    const l = all[i];
    const r = rec(id);
    const next = all[i + 1];
    C.$app.innerHTML = `
      <div class="topbar"><a class="icon-btn" href="#/grammar" aria-label="回課程表">${C.I.back()}</a><span class="title">${C.esc(G.title)}・第 ${i + 1} 課</span></div>
      <header class="lt-head"><h1 data-fit="22">${rich(l.title)}</h1><p data-fit="12">${rich(l.sub)}${r.best != null ? `，練習最佳 ${r.best}/${r.total}` : ''}</p></header>
      <div class="panel gm-sum">${rich(l.summary)}
        <div class="gm-formula">${l.formula.map((f) => `<span class="gm-chip">${rich(f)}</span>`).join('')}</div>
      </div>
      <div class="panel gm-body">${l.body.map((p) => `<p>${rich(p)}</p>`).join('')}</div>
      ${l.table ? tableHTML(l.table) : ''}
      <h2 class="group-title">例句<small>點一下就能聽</small></h2>
      <div class="panel gm-exs">${l.ex.map((e) => `<div class="gm-ex" data-gm-say="${e.a}" role="button" tabindex="0" aria-label="播放：${C.esc(plain(e.ko))}">
        <div class="gm-ko" lang="ko">${hl(e.ko)}</div><div class="gm-zh">${C.esc(e.zh)}</div>${speaker(e.a)}
      </div>`).join('')}</div>
      <div class="panel lt-notes gm-notes"><h2>小提醒</h2><ul>${l.notes.map((x) => `<li>${rich(x)}</li>`).join('')}</ul></div>
      <div class="dock"><div class="dock-inner">
        <a class="pill" href="#/grammar/${l.id}/practice">練習這一課</a>
        ${next ? `<a class="pill ghost" href="#/grammar/${next.id}">下一課</a>` : '<a class="pill ghost" href="#/grammar">課程表</a>'}
      </div></div>`;
  });
}

/* ---------- 練習 ---------- */
function shuffle(a) {
  for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
  return a;
}

function buildPractice(l) {
  const qs = l.quiz.map((q) => ({
    type: q.s ? 'cloze' : 'pick', q, au: q.au, zh: q.zh,
    full: q.s ? q.s.replace('___', q.o[q.a]) : q.o[q.a],
    opts: shuffle(q.o.map((t, k) => ({ t, ok: k === q.a }))), picked: null,
  }));
  // 聽力：用這一課的例句，從其他例句的中文裡挑干擾選項
  shuffle(l.ex.slice()).slice(0, 3).forEach((e) => {
    const others = shuffle(l.ex.filter((x) => x.zh !== e.zh)).slice(0, 3);
    qs.push({
      type: 'listen', au: e.a, zh: e.zh, full: plain(e.ko),
      opts: shuffle([{ t: e.zh, ok: true }, ...others.map((x) => ({ t: x.zh, ok: false }))]), picked: null,
    });
  });
  return { id: l.id, qs: shuffle(qs), i: 0, right: 0 };
}

export function viewGrammarPractice(id) {
  whenReady(() => {
    const l = lessons().find((x) => x.id === id);
    if (!l) return location.replace('#/grammar');
    if (!prac || prac.id !== id || prac.fresh) prac = buildPractice(l);
    renderPractice(l);
  });
}

const isRight = (q) => q.picked != null && q.opts[q.picked].ok;

function renderPractice(l) {
  if (prac.i >= prac.qs.length) return renderPracticeEnd(l);
  const q = prac.qs[prac.i];
  const answered = q.picked != null;
  let prompt = '';
  if (q.type === 'cloze') {
    const ans = answered ? `<span class="gm-fill ${isRight(q) ? 'ok' : 'ng'}">${C.esc(q.opts.find((o) => o.ok).t)}</span>` : '<span class="gm-blank"></span>';
    prompt = `<div class="gm-q" lang="ko">${C.esc(q.q.s).replace('___', ans)}</div><div class="gm-qzh">${C.esc(q.zh)}</div><div class="ask">選出填入空格的正確寫法</div>`;
  } else if (q.type === 'pick') {
    prompt = `<div class="gm-qzh big">${C.esc(q.zh)}</div><div class="ask">選出正確的韓語句子</div>`;
  } else {
    prompt = `<button class="listen" data-gm-say="${q.au}" aria-label="再聽一次">${C.I.speaker()}</button><div class="ask">聽句子，選出意思</div>`;
  }
  const grid = q.type === 'cloze' && q.opts.length % 2 === 0;
  const tiles = q.opts.map((o, k) => {
    let cls = `tile${q.type === 'cloze' ? '' : ' long'}`;
    let mark = '';
    if (answered) {
      if (o.ok) { cls += ' right'; mark = `<span class="mark">${C.I.check('')}</span>`; }
      else if (q.picked === k) { cls += ' wrong'; mark = `<span class="mark">${C.I.cross('')}</span>`; }
      else cls += ' dim';
    }
    const inner = q.type === 'listen' ? `<span>${C.esc(o.t)}</span>` : `<span class="gm-opt" lang="ko">${C.esc(o.t)}</span>`;
    return `<button class="${cls}" data-gm-pick="${k}" ${answered ? 'disabled' : ''}>${inner}${mark}</button>`;
  }).join('');
  let sheet = '';
  if (answered && !isRight(q)) {
    const [pre, post] = q.type === 'cloze' ? q.q.s.split('___') : [];
    const fixed = q.type === 'cloze' ? `${C.esc(pre)}<em>${C.esc(q.opts.find((o) => o.ok).t)}</em>${C.esc(post)}` : C.esc(q.full);
    sheet = `<div class="sheet ng" role="status"><div class="sheet-inner">
      <div class="sheet-head"><span class="verdict">${C.I.cross('ico')}答錯了</span>${speaker(q.au)}</div>
      <div class="sheet-card gm-fix"><span class="ko" lang="ko">${fixed}</span><span class="zh">${C.esc(q.type === 'listen' ? q.zh : q.zh.replace(/（原形：[^）]*）/, ''))}</span></div>
      ${q.type === 'listen' ? '' : `<p class="gm-why">${rich(q.q.why)}</p>`}
      <button class="pill" data-gm-next>${prac.i === prac.qs.length - 1 ? '看結果' : '下一題'}</button>
    </div></div>`;
  }
  C.$app.innerHTML = `
    <div class="topbar"><a class="icon-btn" href="#/grammar/${l.id}" aria-label="結束練習">${C.I.close()}</a><span class="title">${rich(l.title)}・練習</span><span class="count">${prac.i + 1}/${prac.qs.length}</span></div>
    ${C.segsHTML(prac.qs.length, prac.i, (k) => { const a = prac.qs[k]; return a.picked == null ? '' : isRight(a) ? 'ok' : 'ng'; })}
    <div class="stage gm-stage" data-gm-type="${q.type}">
      <div class="prompt">${prompt}</div>
      <div class="tiles${grid ? ' grid' : ''}" role="group" aria-label="選項">${tiles}</div>
    </div>
    ${sheet}`;
  if (!answered && q.type === 'listen') C.playFile(url(q.au));
}

function renderPracticeEnd(l) {
  const total = prac.qs.length, right = prac.right;
  const store = C.store;
  store.grammar = store.grammar || {};
  const r = store.grammar[l.id] || {};
  const done = r.done || right / total >= 0.8;
  store.grammar[l.id] = { best: Math.max(r.best || 0, right), total, done, at: Date.now() };
  C.save();
  prac.fresh = true;
  const all = lessons();
  const next = all[all.indexOf(l) + 1];
  const wrong = prac.qs.filter((q) => !isRight(q));
  C.$app.innerHTML = `
    <div class="topbar"><a class="icon-btn" href="#/grammar" aria-label="回課程表">${C.I.close()}</a><span class="title">${rich(l.title)}・練習</span></div>
    <section class="terminal">
      <div class="score">${right}<small>/${total}</small></div>
      <p>${right === total ? '全部答對！' : done ? '這一課學完了，答錯的句子再聽幾次。' : '答對八成就算學完，回去看一下重點再練一次吧。'}</p>
    </section>
    ${wrong.length ? `<h2 class="group-title">答錯的題目</h2><div class="panel gm-exs">${wrong.map((q) => `<div class="gm-ex" data-gm-say="${q.au}" role="button" tabindex="0">
      <div class="gm-ko" lang="ko">${C.esc(q.full)}</div><div class="gm-zh">${C.esc(q.zh.replace(/（原形：[^）]*）/, ''))}</div>${speaker(q.au)}
    </div>`).join('')}</div>` : ''}
    <div class="dock"><div class="dock-inner">
      <button class="pill ghost" data-gm-again>再練一次</button>
      ${done && next ? `<a class="pill" href="#/grammar/${next.id}">下一課</a>` : `<a class="pill" href="#/grammar/${l.id}">回到這一課</a>`}
    </div></div>`;
}

function pick(k) {
  const q = prac && prac.qs[prac.i];
  if (!q || q.picked != null) return;
  q.picked = k;
  const ok = q.opts[k].ok;
  if (ok) prac.right += 1;
  const l = lessons().find((x) => x.id === prac.id);
  renderPractice(l);
  if (q.type !== 'listen') C.playFile(url(q.au));   // 作答後把整句念一次
  const here = location.hash;
  if (ok) setTimeout(() => { if (prac.qs[prac.i] === q && location.hash === here) { prac.i += 1; renderPractice(l); } }, q.type === 'listen' ? 750 : 1300);
}

/* ---------- 事件 ---------- */
document.addEventListener('click', (e) => {
  const el = e.target.closest('[data-gm-say],[data-gm-pick],[data-gm-next],[data-gm-again]');
  if (!el || !C) return;
  const d = el.dataset;
  if (d.gmAgain !== undefined) {
    const l = lessons().find((x) => x.id === prac.id);
    prac = buildPractice(l); renderPractice(l); window.scrollTo(0, 0);
    return;
  }
  if (d.gmSay !== undefined) {
    const btn = el.classList.contains('d-say') || el.classList.contains('listen') ? el : el.querySelector('.d-say');
    C.playFile(url(d.gmSay), btn);
    return;
  }
  if (d.gmPick !== undefined) { pick(+d.gmPick); return; }
  if (d.gmNext !== undefined) { prac.i += 1; renderPractice(lessons().find((x) => x.id === prac.id)); }
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    const ex = e.target.closest && e.target.closest('.gm-ex');
    if (ex && C) { e.preventDefault(); ex.click(); return; }
  }
  if (!prac || !/^#\/grammar\/\w+\/practice$/.test(location.hash)) return;
  const k = '1234'.indexOf(e.key);
  if (k >= 0) pick(k);
  if (e.key === 'Enter') { const b = document.querySelector('[data-gm-next]'); if (b) b.click(); }
});
