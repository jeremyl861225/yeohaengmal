"""把各來源詞表正規化成「詞條鍵」並計算收錄數（旅遊實用頻率）。韓文版。

詞條鍵：w:<KRDict 詞條 id>（字典查得到的詞；活用形用 kiwipiepy 還原原形：갈아타요→갈아타다、감사합니다→감사하다）
        p:<只留韓文數字的句子>（句子、字典沒有的詞）
只有羅馬拼音沒有韓文的條目：用 KRDict 單字的官方拼音（寬鬆鍵）比對，唯一對上才收，其餘丟掉並計數。
輸出 build/candidates.json、ambiguous.json、sources_meta.json、dropped_rom.json。
"""
import collections, glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from kiwipiepy import Kiwi
from wordfreq import zipf_frequency

entries, by_w, by_id = krdict()
kiwi = Kiwi()

PAREN_RE = re.compile(r"[（(]([^）)]*)[）)]")
BRACKET_RE = re.compile(r"[［\[]([^］\]]*)[］\]]")
QUOTES = "「」『』\"“”'‘’"
CONTENT = {"NNG", "NNP", "NP", "NR", "VV", "VA", "VX", "MAG", "MAJ", "MM", "IC", "XR", "SL", "SN"}


def clean(s):
    s = (s or "").replace("​", "").strip().strip(QUOTES).strip()
    return re.sub(r"\s+", " ", s)


def split_forms(item):
    """一個來源條目 → 可能的韓文寫法（第一個是主要寫法）、來源給的發音、括號裡的漢字"""
    t = clean(item.get("t", ""))
    pron = clean(item.get("pron", "")).strip("［］[]")
    hanja = ""
    m = BRACKET_RE.search(t)
    if m and has_hangul(m.group(1)):
        pron = pron or m.group(1).strip()
        t = BRACKET_RE.sub("", t).strip()
    for m in PAREN_RE.finditer(t):
        inner = m.group(1).strip()
        if HANJA_RE.search(inner) and not has_hangul(inner):
            hanja = inner
    t = PAREN_RE.sub(lambda m: "" if not has_hangul(m.group(1)) else m.group(0), t).strip()
    forms = []
    for alt in re.split(r"\s*[／/]\s*", t):
        alt = alt.strip().strip(".,;:·")
        if alt and has_hangul(alt):
            forms.append(alt)
    return forms, pron, hanja


def lemma_of(text):
    """單一個詞加語尾 → 原形（갈아타요→갈아타다、예약했어요→예약하다、화장실이→화장실）；不是單一個詞就回傳 None"""
    toks = kiwi.tokenize(text)
    core = [t for t in toks if t.tag.split("-")[0] in CONTENT or t.tag.startswith("XS")]
    if not core:
        return None
    tags = [t.tag.split("-")[0] for t in core]
    if len(core) == 1:
        t = core[0]
        return t.form + "다" if tags[0] in ("VV", "VA", "VX") else t.form
    if len(core) == 2 and tags[0] in ("NNG", "NNP", "XR") and tags[1] in ("XSV", "XSA"):
        return core[0].form + core[1].form + "다"
    return None


def pick_best(cands, meaning, lang, hanja):
    """同形異義：初級優先；英文來源比對英文對譯；中文來源比對漢字；來源括號寫了漢字就直接用"""
    if hanja:
        hit = [c for c in cands if c["origin"] and hanja in c["origin"].replace(" ", "")]
        if hit:
            return hit[:1]
    scored = []
    mwords = {w for w in re.findall(r"[a-z]+", (meaning or "").lower()) if len(w) > 2}
    mchars = set(HANJA_RE.findall(meaning or ""))
    for c in cands:
        s = LEVEL_SCORE.get(c["level"], 0) + (1 if c["unit"] == "단어" else 0)
        if mwords:
            g = " ".join(c["en"]).lower()
            s += 2 * len([w for w in mwords if w in g])
        if mchars:
            kan = set(HANJA_RE.findall(c["origin"] + "".join(c["ja"])))
            s += 2 * len(mchars & kan)
        scored.append((s, -c["hn"], c))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    top = scored[0][0]
    return [c for s, _, c in scored if s == top]


def resolve(form, meaning, lang, hanja):
    """回傳 ('w', 詞條id) 或 ('p', 句子鍵) 或 ('?', [id...])"""
    cands = by_w.get(form, [])
    if not cands and " " not in form.strip():
        lem = lemma_of(form)
        if lem and lem != form:
            cands = by_w.get(lem, [])
    cands = [c for c in cands if c["unit"] in ("단어", "")] or cands
    if len(cands) > 1:
        cands = pick_best(cands, meaning, lang, hanja)
    if len(cands) == 1:
        return ("w", cands[0]["id"])
    if len(cands) > 1:
        return ("?", [c["id"] for c in cands])
    key = norm_key(form)
    return ("p", key) if key else None


def main():
    agg, unresolved, src_meta = {}, [], []
    dropped_rom = collections.Counter()
    ridx = None
    for f in sorted(glob.glob(os.path.join(SOURCES, "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        sid, lang = d["id"], d.get("lang", "")
        src_meta.append({"id": sid, "lang": lang, "title": d.get("title", ""), "url": d.get("url", ""), "n_items": len(d["items"])})
        for it in d["items"]:
            forms, pron, hanja = split_forms(it)
            meaning = it.get("meaning", "")
            if not forms and it.get("rom"):
                ridx = ridx or roma_index()
                hits = ridx.get(loose_roma(it["rom"]), [])
                hits = [h for h in hits if h["level"] in ("초급", "중급")] or hits
                if len(hits) == 1:
                    forms = [hits[0]["w"]]
                else:
                    dropped_rom[sid] += 1
                    continue
            for form in forms[:2]:
                res = resolve(form, meaning, lang, hanja)
                if not res:
                    continue
                kind, key = res
                if kind == "?":
                    unresolved.append({"src": sid, "form": form, "meaning": meaning, "cands": [(c, by_id[c]["origin"], by_id[c]["en"][:1]) for c in key]})
                    key, kind = key[0], "w"
                k = f"{kind}:{key}"
                a = agg.setdefault(k, {"key": k, "kind": kind, "sources": set(), "forms": collections.Counter(), "pron": collections.Counter(),
                                       "meanings": {}, "sections": collections.Counter()})
                a["sources"].add(sid)
                a["forms"][form] += 1
                if pron:
                    a["pron"][pron] += 1
                if meaning:
                    a["meanings"].setdefault(lang, []).append(meaning)
                if it.get("section"):
                    a["sections"][f"{sid}:{it['section']}"] += 1
    out = []
    for a in agg.values():
        rec = {"key": a["key"], "kind": a["kind"], "n": len(a["sources"]), "sources": sorted(a["sources"]),
               "forms": [f for f, _ in a["forms"].most_common()], "src_pron": [p for p, _ in a["pron"].most_common()],
               "meanings": {k: list(dict.fromkeys(v))[:6] for k, v in a["meanings"].items() if v},
               "sections": [s for s, _ in a["sections"].most_common(8)]}
        rec["head"] = rec["forms"][0]            # 來源最常用的寫法（감사합니다，不是字典的 감사하다）
        if a["kind"] == "w":
            e = by_id[a["key"][2:]]
            rec.update({"kd": e["id"], "lemma": e["w"], "lemma_pron": e["pron1"], "origin": e["origin"], "pos": e["pos"],
                        "level": e["level"], "gloss": e["en"][:6], "sem": e["sem"]})
        rec["zipf"] = zipf_frequency(rec["head"], "ko")
        out.append(rec)
    out.sort(key=lambda r: (-r["n"], -r["zipf"]))
    os.makedirs(BUILD, exist_ok=True)
    json.dump(out, open(os.path.join(BUILD, "candidates.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(unresolved, open(os.path.join(BUILD, "ambiguous.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(src_meta, open(os.path.join(BUILD, "sources_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(dropped_rom, open(os.path.join(BUILD, "dropped_rom.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    dist = collections.Counter(r["n"] for r in out)
    print(f"{len(src_meta)} 份來源 → {len(out)} 個詞條（詞 {sum(1 for r in out if r['kind']=='w')}、句 {sum(1 for r in out if r['kind']=='p')}），"
          f"多義待判 {len(unresolved)}，只有拼音對不上而丟掉 {sum(dropped_rom.values())}")
    print("收錄數分佈:", sorted(dist.items(), reverse=True))


if __name__ == "__main__":
    main()
