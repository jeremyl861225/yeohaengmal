"""離線字典 data/dict.json：KRDict（國立國語院《韓國語基礎辭典》，CC BY-SA 2.0 KR）常用詞子集，補字卡以外的字。
收錄：初級＋中級全部，其餘難度取一般語料詞頻 Zipf ≥ YH_DICT_ZIPF（預設 3.4）。
條目：{w 韓文, h 漢字（純漢字段）, p 詞性（中文）, g 英文對譯, m 官方羅馬拼音}。KRDict 2019 年版沒有中文對譯，所以沒有 z 欄。
搜尋規則在 js/dict.js（相容字母前綴、初聲、漢字、英文、羅馬拼音）。"""
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline"))
from common import *
from rr import romanize
from wordfreq import zipf_frequency

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIPF = float(os.environ.get("YH_DICT_ZIPF", 3.4))
POS = {"명사": "名詞", "동사": "動詞", "형용사": "形容詞", "부사": "副詞", "대명사": "代名詞", "수사": "數詞", "관형사": "冠形詞",
       "감탄사": "感嘆詞", "의존 명사": "依存名詞", "보조 동사": "補助動詞", "보조 형용사": "補助形容詞", "조사": "助詞"}


def hanja_of(origin):
    """原語欄只留漢字段（安寧 하다 → 安寧；空港bus → 空港）；外來語的語源註記不收"""
    if not origin or "[" in origin or "←" in origin:
        return ""
    origin = re.sub(r"([㐀-鿿豈-﫿]+)(?:/[㐀-鿿豈-﫿]+)+", r"\1", origin.replace("▽", ""))
    return "".join(re.findall(r"[㐀-鿿豈-﫿]+", origin))


def main():
    entries, _, _ = krdict()
    seen, out = set(), []
    for e in entries:
        if e["unit"] != "단어" or "-" in e["w"] or not e["en"] or not has_hangul(e["w"]):
            continue
        if e["level"] not in ("초급", "중급") and zipf_frequency(e["w"], "ko") < ZIPF:
            continue
        if e["pos"] == "조사":
            continue      # 助詞的英文對譯只是拼音（가 → ga），查了也沒用
        m = romanize(e["w"], e["pron1"] or None)
        # 英文對譯有時就是拼音（호텔 → hotel、김치 → kimchi），照收：用英文查得到
        g = "; ".join(dict.fromkeys(x.strip() for x in e["en"][:3] if x.strip()))
        if not g:
            continue
        k = (e["w"], g)
        if k in seen:
            continue
        seen.add(k)
        d = {"w": e["w"], "g": g}
        h = hanja_of(e["origin"])
        if h:
            d["h"] = h
        if POS.get(e["pos"]):
            d["p"] = POS[e["pos"]]
        d["m"] = m
        out.append(d)
    data = {"source": "國立國語院《韓國語基礎辭典》（krdict.korean.go.kr，CC BY-SA 2.0 KR）常用詞，英文對譯", "entries": out}
    path = os.path.join(ROOT, "data", "dict.json")
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(out)} 條 → data/dict.json（{os.path.getsize(path) / 1024:.0f} KB）")


if __name__ == "__main__":
    main()
