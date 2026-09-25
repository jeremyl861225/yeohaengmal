"""離線字典：從 JMdict 常用詞版（jmdict-eng-common，約 2.2 萬詞）抽出寫法、讀音、詞性、英文釋義，
輸出 data/dict.json 給 App 查字卡以外的字。資料授權 CC BY-SA 4.0（EDRDG），衍生檔沿用同授權。
"""
import json, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get("TK_WORK", os.path.expanduser("~/Desktop/Claude code/workspace/work/jp-travel-vocab"))
SRC = sorted(glob.glob(os.path.join(WORK, "dict", "jmdict-eng-common-*.json")))[-1]

POS = [("v5", "動詞"), ("v1", "動詞"), ("vk", "動詞"), ("vs-", "動詞"), ("vz", "動詞"), ("adj-i", "い形容詞"), ("adj-na", "な形容詞"),
       ("adv", "副詞"), ("int", "感嘆詞"), ("pn", "代名詞"), ("ctr", "量詞"), ("num", "數詞"), ("prt", "助詞"), ("exp", "連語"),
       ("suf", "接尾詞"), ("pref", "接頭詞"), ("aux", "助動詞"), ("conj", "接續詞"), ("adj-pn", "連體詞"), ("n", "名詞")]


def pos_label(codes):
    for c in codes:
        for k, v in POS:
            if c == k or c.startswith(k):
                if c == "vs":
                    return "名詞（する動詞）"
                return v
    return ""


def main():
    data = json.load(open(SRC, encoding="utf-8"))
    out = []
    for w in data["words"]:
        kanji = [k["text"] for k in w["kanji"] if k.get("common")] or [k["text"] for k in w["kanji"]][:1]
        kana = [r["text"] for r in w["kana"] if r.get("common")] or [r["text"] for r in w["kana"]][:1]
        senses = w["sense"][:3]
        uk = any("uk" in s.get("misc", []) for s in senses[:1])
        gl = []
        for s in senses:
            g = ", ".join(x["text"] for x in s["gloss"][:3])
            if g and g not in gl:
                gl.append(g)
        gloss = "; ".join(gl)
        if len(gloss) > 90:
            gloss = gloss[:88].rsplit(",", 1)[0] + "…"
        e = {"k": kanji[:2], "r": kana[:2], "g": gloss, "p": pos_label(senses[0].get("partOfSpeech", []) if senses else [])}
        if uk:
            e["u"] = 1  # 平常寫假名
        if not e["k"]:
            del e["k"]
        out.append(e)
    dst = os.path.join(ROOT, "data", "dict.json")
    json.dump({"source": "JMdict (EDRDG), CC BY-SA 4.0, common entries", "entries": out}, open(dst, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"{len(out)} 詞 → data/dict.json（{os.path.getsize(dst) / 1024:.0f} KB）")


if __name__ == "__main__":
    main()
