"""韓文襯線字子集：Noto Serif KR（SIL OFL 1.1）依字卡實際用到的字裁切成 woff2，打包進 App。
為什麼打包：iPhone 沒有內建韓文明朝體，沒打包的話韓文會整片變黑體（Mac 有 AppleMyungjo，在 Mac 上看不出來）。
- fonts/ko-serif.woff2：400，字卡（寫法、例句、唸法）與介面用到的韓文＋ASCII＋常用標點
- fonts/ko-serif-600.woff2：600，只有品牌字與開場字（여행말、旅）
字典的字不在子集裡，退回系統字（CSS 的字型堆疊）。資料改了要重跑，並升 sw.js 的 CACHE_VERSION。
原始字型：Google Fonts 的可變字型 NotoSerifKR[wght].ttf，放在工作區 fonts/（不進 repo）。"""
import json, os, re, sys
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get("YH_WORK", os.path.expanduser("~/Desktop/Claude code/workspace/work/ko-travel-vocab"))
SRC = os.path.join(WORK, "fonts", "NotoSerifKR-VF.ttf")
OUT = os.path.join(ROOT, "fonts")
RUBY = re.compile(r"\{([^|{}]+)\|[^{}]+\}")
UI_TEXT = "여행말도착종점가치공항［］"          # app.js 裡寫死的韓文（品牌、到站、終點、設定頁的例子）
BRAND = "여행말旅"


def card_text():
    with open(os.path.join(ROOT, "data", "cards.json"), encoding="utf-8") as f:
        d = json.load(f)
    parts = []
    for c in d["cards"]:
        parts += [RUBY.sub(r"\1", c["w"]), c.get("r", ""), c.get("ex", "")]
    return "".join(parts)


def build(text, weight, out):
    font = TTFont(SRC)
    opts = subset.Options()
    # 直排特徵會讓裁切出錯（KeyError 'uni…vert'），韓文橫排也用不到
    opts.layout_features = ["kern", "ccmp", "locl", "liga", "calt"]
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(text=text)
    sub.subset(font)
    instancer.instantiateVariableFont(font, {"wght": weight}, inplace=True)
    font.flavor = "woff2"
    font.save(out)
    return os.path.getsize(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    ascii_ = "".join(chr(i) for i in range(0x20, 0x7F))
    punct = "“”‘’…·、。，．！？（）「」『』～〜・—–％"
    chars = set(card_text() + UI_TEXT + ascii_ + punct)
    hangul = sorted(ch for ch in chars if "가" <= ch <= "힣")
    n400 = build("".join(sorted(chars)), 400, os.path.join(OUT, "ko-serif.woff2"))
    n600 = build(BRAND, 600, os.path.join(OUT, "ko-serif-600.woff2"))
    with open(os.path.join(WORK, "fonts", "OFL.txt"), encoding="utf-8") as f:
        lic = f.read()
    with open(os.path.join(OUT, "OFL.txt"), "w", encoding="utf-8") as f:
        f.write(lic)
    print(f"韓文音節 {len(hangul)} 個；ko-serif.woff2 {n400/1024:.0f} KB、ko-serif-600.woff2 {n600/1024:.0f} KB")


if __name__ == "__main__":
    main()
