// 離線字典：韓國語基礎辭典（KRDict）常用詞，英文釋義（有中文對譯時一起顯示），補字卡以外的字。第一次查詢時才載入。
// 條目：{w 韓文, h 漢字, p 詞性, g 英文釋義, z 中文, m 羅馬拼音}
import { jamo, chosung, isChosungQuery, normQuery, romaKey, hasHangul } from './ruby.js';

let DICT = null;
let loading = null;

export function loadDict() {
  if (DICT) return Promise.resolve(DICT);
  if (!loading) {
    loading = fetch('data/dict.json')
      .then((r) => r.json())
      .then((d) => {
        DICT = d.entries.map((e) => {
          const g = (e.g || '').toLowerCase();
          const w = normQuery(e.w);
          return { ...e, _w: w, _j: jamo(w), _c: chosung(w), _rk: e.m ? romaKey(e.m) : '', _g: ` ${g.replace(/[^a-z0-9 ]+/g, ' ')} `, _g1: g.split(/[;,]/)[0].replace(/\(.*?\)/g, '').trim() };
        });
        return DICT;
      })
      .catch((err) => { loading = null; throw err; });
  }
  return loading;
}

export const dictReady = () => !!DICT;

// 回傳 [{e, score}]，score 越小越前面；exclude 是已經有字卡的寫法
export function searchDict(query, exclude, limit = 30) {
  if (!DICT) return [];
  const q = query.trim();
  if (!q) return [];
  const ascii = /^[\x20-\x7eÀ-ſ]+$/.test(q);
  const qn = normQuery(q);
  const hangul = !ascii && hasHangul(qn);
  const qj = hangul ? jamo(qn) : '';
  const cho = hangul && isChosungQuery(qn);
  const rk = ascii ? romaKey(q) : '';
  const eng = ascii ? q.toLowerCase().replace(/[^a-z0-9 ]+/g, ' ').trim() : null;
  const out = [];
  for (const e of DICT) {
    if (exclude.has(e._w)) continue;
    let score = 9;
    if (hangul) {
      if (e._w === qn) score = 0;
      else if (cho && e._c.startsWith(qn)) score = 1.5;
      else if (e._j.startsWith(qj)) score = 1;
      else if ([...qn].length >= 2 && e._w.includes(qn)) score = 2;
    } else if (!ascii) {
      // 中文或漢字：空港、機場
      if (e.h && e.h === q) score = 0;
      else if (e.z && e.z.split(/[；;，,、]/).some((x) => x.trim() === q)) score = 0.5;
      else if (e.h && e.h.startsWith(q)) score = 1;
      else if (e.z && e.z.includes(q)) score = 1.5;
      else if (e.h && q.length >= 2 && e.h.includes(q)) score = 2;
    } else {
      if (rk.length >= 3 && e._rk) {
        if (e._rk === rk) score = 0;
        else if (e._rk.startsWith(rk)) score = 1;
      }
      if (score > 3 && eng && eng.length >= 3) {
        if (e._g1 === eng || e._g1 === `to ${eng}`) score = 2;          // 第一個釋義就是它
        else if (e._g.includes(` ${eng} `)) score = 2.5;
        else if (e._g.includes(` ${eng}`)) score = 3;
      }
    }
    if (score < 9) out.push({ e, score });
  }
  out.sort((a, b) => a.score - b.score || a.e.w.length - b.e.w.length);
  return out.slice(0, limit);
}
