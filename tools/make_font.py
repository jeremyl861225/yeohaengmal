"""字型子集（2026-10-02 起套用旅ことば的「暮色玻璃」外觀）：
- 韓文：Noto Serif KR（SIL OFL 1.1）可變字型取 500、900 兩個字重，依字卡與介面用到的字裁切。
  iPhone 沒有內建韓文明朝體，沒打包的話韓文會整片變黑體（Mac 有 AppleMyungjo，在 Mac 上看不出來）。
  fonts/ko-serif-500.woff2（字卡、例句、唸法、介面）、fonts/ko-serif-900.woff2（字卡大字、品牌、標題）
- 中文標題、數字、小標籤：Zen Old Mincho（SIL OFL 1.1，旅ことば同一套字），只收介面用到的字（站名、主題、家族、App 裡寫死的字）。
  fonts/zenold-500.woff2、fonts/zenold-900.woff2。中文內文（意思、例句翻譯）仍用系統宋體。
字典的字不在子集裡，退回系統字（CSS 的字型堆疊）。資料或介面文字改了要重跑，並升 sw.js 的 CACHE_VERSION。
原始字型放在工作區（不進 repo）：ko-travel-vocab/fonts/NotoSerifKR-VF.ttf、jp-travel-vocab/fonts/zenold/ZenOldMincho-{Medium,Black}.ttf。"""
import json, os, re, glob
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get("YH_WORK", os.path.expanduser("~/Desktop/Claude code/workspace/work/ko-travel-vocab"))
SRC = os.path.join(WORK, "fonts", "NotoSerifKR-VF.ttf")
ZEN = os.path.join(os.path.dirname(WORK), "jp-travel-vocab", "fonts", "zenold")
OUT = os.path.join(ROOT, "fonts")
RUBY = re.compile(r"\{([^|{}]+)\|[^{}]+\}")
ASCII = "".join(chr(i) for i in range(0x20, 0x7F))
PUNCT = "“”‘’…·、。，．！？（）「」『』～〜・—–％／：；＋×［］"


def is_hangul(ch):
    return "가" <= ch <= "힣" or "㄰" <= ch <= "㆏" or "ᄀ" <= ch <= "ᇿ"


def data():
    with open(os.path.join(ROOT, "data", "cards.json"), encoding="utf-8") as f:
        return json.load(f)


def ui_text():
    """App 裡寫死的字：index.html、js/*.js、四十音課程（data/letters.json）、文法專欄（data/grammar.json）"""
    parts = [open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()]
    for name in ("letters", "grammar"):
        parts.append(open(os.path.join(ROOT, "data", f"{name}.json"), encoding="utf-8").read())
    for p in glob.glob(os.path.join(ROOT, "js", "*.js")):
        parts.append(open(p, encoding="utf-8").read())
    return "".join(parts)


def korean_chars(d, ui):
    parts = [ui]
    for c in d["cards"]:
        parts += [RUBY.sub(r"\1", c["w"]), c.get("r", ""), c.get("pr", ""), RUBY.sub(r"\1", c.get("ex", "") or "")]
    for t in d["themes"]:
        parts.append(t.get("ja", ""))   # 韓文路線名
    return {ch for ch in "".join(parts) if is_hangul(ch)}


def zen_chars(d, ui):
    """標題、站名、家族、數字、介面字（不含意思與例句翻譯：那些用系統宋體）"""
    parts = [ui]
    parts += [t["name"] for t in d["themes"]] + [u["title"] for u in d["units"]]
    parts += [t["name"] for t in d["tiers"]] + [f["name"] for f in d.get("families", [])]
    return {ch for ch in "".join(parts) if not is_hangul(ch) and ord(ch) > 0x7F}


def build(src, text, out, wght=None):
    font = TTFont(src)
    opts = subset.Options()
    # 直排特徵會讓裁切出錯（KeyError 'uni…vert'），橫排也用不到
    opts.layout_features = ["kern", "ccmp", "locl", "liga", "calt", "palt"]
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(text=text)
    sub.subset(font)
    if wght:
        instancer.instantiateVariableFont(font, {"wght": wght}, inplace=True)
    font.flavor = "woff2"
    font.save(out)
    return os.path.getsize(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    d, ui = data(), ui_text()
    ko = "".join(sorted(korean_chars(d, ui))) + ASCII + PUNCT
    zen = "".join(sorted(zen_chars(d, ui))) + ASCII + PUNCT
    sizes = {
        "ko-serif-500.woff2": build(SRC, ko, os.path.join(OUT, "ko-serif-500.woff2"), 500),
        "ko-serif-900.woff2": build(SRC, ko, os.path.join(OUT, "ko-serif-900.woff2"), 900),
        "zenold-500.woff2": build(os.path.join(ZEN, "ZenOldMincho-Medium.ttf"), zen, os.path.join(OUT, "zenold-500.woff2")),
        "zenold-900.woff2": build(os.path.join(ZEN, "ZenOldMincho-Black.ttf"), zen, os.path.join(OUT, "zenold-900.woff2")),
    }
    for old in ("ko-serif.woff2", "ko-serif-600.woff2"):
        p = os.path.join(OUT, old)
        if os.path.exists(p):
            os.remove(p)
    with open(os.path.join(WORK, "fonts", "OFL.txt"), encoding="utf-8") as f:
        open(os.path.join(OUT, "OFL.txt"), "w", encoding="utf-8").write(f.read())
    with open(os.path.join(ZEN, "OFL.txt"), encoding="utf-8") as f:
        open(os.path.join(OUT, "OFL-ZenOldMincho.txt"), "w", encoding="utf-8").write(f.read())
    print(f"韓文 {len(ko) - len(ASCII) - len(PUNCT)} 字、Zen Old Mincho {len(zen) - len(ASCII) - len(PUNCT)} 字；"
          + "、".join(f"{k} {v / 1024:.0f} KB" for k, v in sizes.items()))


if __name__ == "__main__":
    main()
