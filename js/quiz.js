// 出題：八種題型。選擇題的干擾選項優先從同主題、同等級挑；拼字題用音節方塊。
import { plain, isHangulText, parts, compose } from './ruby.js';

export const TYPES = {
  k2z: '看韓文選中文',
  z2k: '看中文選韓文',
  pron: '看韓文選實際唸法',
  aud: '聽發音選單字',
  audz: '聽發音選中文',
  exl: '聽例句選意思',
  spell: '拼出韓文',
  dict: '聽寫',
};
export const TYPE_HINT = {
  k2z: '出現韓文，選中文意思',
  z2k: '出現中文，選韓文單字',
  pron: '寫法和唸法不同的字（같이 唸［가치］），選出實際唸法',
  aud: '只播放發音，選聽到的單字',
  audz: '只播放發音，選中文意思',
  exl: '播放整句例句，選它的中文意思',
  spell: '看中文意思，用音節方塊拼出韓文',
  dict: '只播放發音，用音節方塊拼出聽到的字',
};
export const TYPE_GROUPS = [
  ['看字', ['k2z', 'z2k', 'pron']],
  ['聽力', ['aud', 'audz', 'exl', 'dict']],
  ['拼字', ['spell']],
];

function shuffle(a) {
  const b = a.slice();
  for (let i = b.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [b[i], b[j]] = [b[j], b[i]];
  }
  return b;
}

const zhKey = (c) => c.zh.split(/[、，,；;／/（(]/)[0].trim();
// 拼字題考寫法：單字、2–10 個音節、全是韓文音節（沒有空格、數字、英文）
export const spellable = (card) => {
  const w = plain(card.w);
  return card.k !== 'p' && isHangulText(w) && [...w].length >= 2 && [...w].length <= 10;
};
// 實際唸法和寫法不同的字才出「看韓文選實際唸法」
const pronDiffers = (card) => card.k !== 'p' && card.r && card.r !== plain(card.w).replace(/\s/g, '') && isHangulText(card.r) && [...card.r].length <= 10;

function eligible(card, type) {
  if (type === 'pron') return pronDiffers(card);
  if (type === 'spell' || type === 'dict') return spellable(card);
  if (type === 'exl') return !!(card.ex && card.exz);
  return true;
}

// 從候選池挑 n 個不衝突的干擾卡
function pickDistractors(card, pool, n, conflict) {
  const tiers = [
    pool.filter((c) => c.th === card.th && c.t === card.t),
    pool.filter((c) => c.th === card.th),
    pool.filter((c) => c.t === card.t),
    pool,
  ];
  const chosen = [];
  for (const group of tiers) {
    for (const c of shuffle(group)) {
      if (chosen.length >= n) break;
      if (c.id === card.id || chosen.includes(c)) continue;
      if (conflict(c, card) || chosen.some((x) => conflict(c, x))) continue;
      chosen.push(c);
    }
    if (chosen.length >= n) break;
  }
  return chosen;
}

const sameMeaning = (a, b) => zhKey(a) === zhKey(b) || a.zh === b.zh;
const sameWord = (a, b) => plain(a.w) === plain(b.w) || a.r === b.r;
const sameEx = (a, b) => !a.exz || !b.exz || a.exz === b.exz;

/* ---------- 音節的近似錯誤：換掉一個成分 ----------
   初聲：平音／緊音／送氣音（ㄱㄲㅋ、ㄷㄸㅌ、ㅂㅃㅍ、ㅈㅉㅊ、ㅅㅆ）、ㄴ/ㄹ、ㅇ/ㅎ
   中聲：ㅓ/ㅗ、ㅐ/ㅔ、ㅡ/ㅜ、ㅕ/ㅛ…　終聲：有無收尾音、ㄴ/ㅇ、ㄱ/ㅂ/ㄷ */
const L_NEAR = { 0: [1, 15], 1: [0, 15], 15: [0, 1], 3: [4, 16], 4: [3, 16], 16: [3, 4], 7: [8, 17], 8: [7, 17], 17: [7, 8],
  12: [13, 14], 13: [12, 14], 14: [12, 13], 9: [10], 10: [9], 2: [5], 5: [2], 11: [18], 18: [11], 6: [7] };
const V_NEAR = { 0: [4], 1: [5], 2: [6], 3: [7], 4: [8, 0], 5: [1], 6: [12, 2], 7: [3], 8: [4, 13], 9: [14], 10: [11, 15],
  11: [10, 15], 12: [6], 13: [18, 8], 14: [9], 15: [10, 11], 16: [13], 17: [12], 18: [13], 19: [20, 18], 20: [19] };
const T_NEAR = { 0: [4, 21, 8], 1: [17, 7], 4: [21, 0], 7: [1, 17, 19], 8: [0], 16: [17, 4], 17: [1, 7, 16], 19: [20, 7],
  20: [19], 21: [4, 0], 22: [23, 7], 23: [22], 27: [0] };

export function nearSyllables(ch) {
  const [l, v, t] = parts(ch);
  const out = [];
  (L_NEAR[l] || []).forEach((x) => out.push(compose(x, v, t)));
  (V_NEAR[v] || []).forEach((x) => out.push(compose(l, x, t)));
  (T_NEAR[t] || []).forEach((x) => out.push(compose(l, v, x)));
  return out;
}

// 把字串裡的一個音節換成近似錯誤
function mutations(s) {
  const chars = [...s];
  const out = new Set();
  chars.forEach((ch, i) => {
    for (const m of nearSyllables(ch)) out.add(chars.slice(0, i).join('') + m + chars.slice(i + 1).join(''));
  });
  out.delete(s);
  return [...out];
}

// 「看韓文選實際唸法」：正解、照寫法唸（最常見的誤會）、換一個音節的近似錯誤，再補別張卡的唸法
function pronOptions(card, pool) {
  const right = card.r;
  const opts = new Set([right]);
  const written = plain(card.w).replace(/\s/g, '');
  if (written !== right) opts.add(written);
  for (const m of shuffle(mutations(right))) {
    if (opts.size >= 4) break;
    opts.add(m);
  }
  for (const c of shuffle(pool)) {
    if (opts.size >= 4) break;
    if (c.id !== card.id && c.k !== 'p' && isHangulText(c.r)) opts.add(c.r);
  }
  return shuffle([...opts]).map((r) => ({ r, right: r === right }));
}

// 音節方塊：寫法的每個音節一塊，再加幾塊長得像的干擾（換一個初聲、中聲或終聲）
export function syllableTiles(word) {
  const chars = [...word];
  const extra = chars.length <= 4 ? 2 : 3;
  const pool = new Set();
  for (const ch of shuffle(chars)) {
    for (const m of shuffle(nearSyllables(ch))) {
      if (!chars.includes(m)) pool.add(m);
      if (pool.size >= extra * 2) break;
    }
    if (pool.size >= extra * 2) break;
  }
  const decoys = shuffle([...pool]).slice(0, extra);
  return shuffle([...chars, ...decoys]).map((ch, i) => ({ ch, i }));
}

export function buildQuiz(scope, pool, types, count) {
  const cards = shuffle(scope).slice(0, Math.min(count, scope.length));
  const useTypes = types.length ? types : Object.keys(TYPES);
  let cycle = [];
  return cards.map((card) => {
    if (!cycle.length) cycle = shuffle(useTypes);
    const fits = (t) => eligible(card, t);
    const type = cycle.find(fits) || useTypes.find(fits) || 'k2z';
    if (cycle.includes(type)) cycle.splice(cycle.indexOf(type), 1);
    const q = { card, type, answer: null };
    if (type === 'pron') {
      q.options = pronOptions(card, pool);
    } else if (type === 'spell' || type === 'dict') {
      q.target = [...plain(card.w)];
      q.tiles = syllableTiles(plain(card.w));
      q.filled = [];
    } else {
      const conflict = type === 'exl' ? sameEx : (type === 'k2z' || type === 'audz') ? sameMeaning : sameWord;
      const ds = pickDistractors(card, pool, 3, (a, b) => sameMeaning(a, b) || sameWord(a, b) || conflict(a, b));
      q.options = shuffle([card, ...ds]).map((c) => ({ c, right: c.id === card.id }));
    }
    return q;
  });
}
