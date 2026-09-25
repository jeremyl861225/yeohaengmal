// 漢字標記：{공항|空港}（漢字標在韓文上方）。其餘文字原樣。
const RUBY_RE = /\{([^|{}]+)\|([^{}]+)\}/g;

export function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

// 轉成 <ruby>；上方的漢字用台灣字形（lang="zh-Hant"）；segments 之外的文字要跳脫
export function rubyHTML(markup) {
  let out = '';
  let last = 0;
  markup.replace(RUBY_RE, (m, base, rt, idx) => {
    out += esc(markup.slice(last, idx));
    out += `<ruby>${esc(base)}<rt lang="zh-Hant">${esc(rt)}</rt></ruby>`;
    last = idx + m.length;
    return m;
  });
  out += esc(markup.slice(last));
  return out;
}

// ​ 是建置時插入的詞組換行點，比對與朗讀時要拿掉
export const plain = (markup) => markup.replace(RUBY_RE, '$1').replace(/​/g, '');
// 上方標的漢字（空港）；沒有漢字就是空字串
export const upper = (markup) => { const out = []; markup.replace(RUBY_RE, (m, b, rt) => { out.push(rt); return m; }); return out.join(''); };
export const hasHanja = (markup) => /\{[^|{}]+\|[^{}]+\}/.test(markup);

/* ---------- 韓文字母 ---------- */
// 音節 = 0xAC00 + (初聲×21 + 中聲)×28 + 終聲。拆成「相容字母」（ㄱ U+3131 那一區，和鍵盤打出來的一樣），不分初聲終聲。
const CHO = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ';
const JUNG = 'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ';
const JONG = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'];
// 複合母音與複合收尾音再拆成基本字母（打字時是分兩下打的）
const SPLIT = { ㅘ: 'ㅗㅏ', ㅙ: 'ㅗㅐ', ㅚ: 'ㅗㅣ', ㅝ: 'ㅜㅓ', ㅞ: 'ㅜㅔ', ㅟ: 'ㅜㅣ', ㅢ: 'ㅡㅣ',
  ㄳ: 'ㄱㅅ', ㄵ: 'ㄴㅈ', ㄶ: 'ㄴㅎ', ㄺ: 'ㄹㄱ', ㄻ: 'ㄹㅁ', ㄼ: 'ㄹㅂ', ㄽ: 'ㄹㅅ', ㄾ: 'ㄹㅌ', ㄿ: 'ㄹㅍ', ㅀ: 'ㄹㅎ', ㅄ: 'ㅂㅅ' };

export const isSyllable = (ch) => { const c = ch.charCodeAt(0); return c >= 0xac00 && c <= 0xd7a3; };
export const isHangulText = (s) => /^[가-힣]+$/.test(s);
export const hasHangul = (s) => /[가-힣ㄱ-ㅣ]/.test(s);

export function parts(ch) {
  const c = ch.charCodeAt(0) - 0xac00;
  return [Math.floor(c / 588), Math.floor((c % 588) / 28), c % 28];
}
export const compose = (l, v, t) => String.fromCharCode(0xac00 + (l * 21 + v) * 28 + t);

// 拆成相容字母序列：공항 → ㄱㅗㅇㅎㅏㅇ；已經是單獨字母的（打到一半的 ㅎ）照收
export function jamo(s) {
  let out = '';
  for (const ch of s) {
    if (isSyllable(ch)) {
      const [l, v, t] = parts(ch);
      out += CHO[l] + (SPLIT[JUNG[v]] || JUNG[v]) + (SPLIT[JONG[t]] || JONG[t]);
    } else if (/[ㄱ-ㅣ]/.test(ch)) {
      out += SPLIT[ch] || ch;
    } else {
      out += ch;
    }
  }
  return out;
}

// 初聲鍵：공항 → ㄱㅎ（韓國人常只打子音查字）
export const chosung = (s) => [...s].map((ch) => (isSyllable(ch) ? CHO[parts(ch)[0]] : '')).join('');
export const isChosungQuery = (s) => /^[ㄱ-ㅎ]{2,}$/.test(s);

// 組合用字母（U+1100 區）→ 相容字母（U+3131 區）
const CONJ_CHO = { 0x1100: 'ㄱ', 0x1101: 'ㄲ', 0x1102: 'ㄴ', 0x1103: 'ㄷ', 0x1104: 'ㄸ', 0x1105: 'ㄹ', 0x1106: 'ㅁ', 0x1107: 'ㅂ', 0x1108: 'ㅃ', 0x1109: 'ㅅ',
  0x110a: 'ㅆ', 0x110b: 'ㅇ', 0x110c: 'ㅈ', 0x110d: 'ㅉ', 0x110e: 'ㅊ', 0x110f: 'ㅋ', 0x1110: 'ㅌ', 0x1111: 'ㅍ', 0x1112: 'ㅎ' };
function toCompat(s) {
  return s.replace(/[ᄀ-ᇿ]/g, (c) => {
    const n = c.charCodeAt(0);
    if (CONJ_CHO[n]) return CONJ_CHO[n];
    if (n >= 0x1161 && n <= 0x1175) return JUNG[n - 0x1161];
    if (n >= 0x11a8 && n <= 0x11c2) return JONG[n - 0x11a7];
    return c;
  });
}

// 搜尋用正規化：全形英數轉半形、去掉空白與標點（韓文分寫習慣常不一致）。
// 不能用 NFKC：它會把鍵盤打出的單獨字母 ㅎ（U+314E）換成組合用字母（U+1112），「공ㅎ」就找不到 공항
export function normQuery(s) {
  return toCompat(s.normalize('NFC'))
    .replace(/[！-～]/g, (c) => String.fromCharCode(c.charCodeAt(0) - 0xfee0))
    .toLowerCase()
    .replace(/[\s.,?!~'"“”‘’·、。，．！？「」『』（）()〜～\-]/g, '');
}

// 羅馬拼音比對鍵：寬鬆比對，讓官方拼法（gamsahamnida）與舊式拼法（kamsahamnida）都對得上
export function romaKey(s) {
  return s
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z]/g, '')
    .replace(/eo/g, 'o').replace(/eu/g, 'u').replace(/ae/g, 'e')
    .replace(/g/g, 'k').replace(/d/g, 't').replace(/b/g, 'p').replace(/j/g, 'ch').replace(/r/g, 'l')
    .replace(/([a-z])\1+/g, '$1');
}

export const isAscii = (s) => /^[\x20-\x7eÀ-ſ]+$/.test(s);
