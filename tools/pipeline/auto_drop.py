"""選字前的規則剔除：明顯不會入選、又會拖慢選字代理的候選，直接寫成刪除決定（build/curate/out-00-auto.json）。
只動只被一份來源收錄的：韓食菜單 800 選裡的冷門菜名、廣播全文的長段落、只有一份來源的長句、一般動詞表裡的冷門字。
來源增加後重跑會重算（被第二份來源收錄的就不再剔除）。"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD

ANN = {"ko-23", "ko-24", "ko-27", "ko-28"}     # 나무위키 的列車、機上、月台、機場廣播全文
MENU = {"ko-26"}                                 # 한식진흥원《한식메뉴 외국어표기 길라잡이 800선》
VERB_LISTS = {"en-06", "ko-03"}                  # 一般動詞表（不是旅遊專題）


def why(c):
    s, syl = set(c["sources"]), len(re.findall(r"[가-힣]", c["head"]))
    if c["n"] != 1:
        return None
    if s <= MENU and c["zipf"] < 3.0:
        return "冷門菜名（只有韓食菜單 800 選收錄）"
    if s <= ANN and syl > 22:
        return "廣播全文太長"
    if c["kind"] == "p" and syl > 16:
        return "只有一份來源的長句"
    if s <= VERB_LISTS and c["zipf"] < 3.5:
        return "一般動詞表裡的冷門字"
    return None


def main():
    cands = json.load(open(os.path.join(BUILD, "candidates.json"), encoding="utf-8"))
    out = [{"key": c["key"], "keep": False, "why": w, "auto": True} for c in cands for w in [why(c)] if w]
    os.makedirs(os.path.join(BUILD, "curate"), exist_ok=True)
    json.dump(out, open(os.path.join(BUILD, "curate", "out-00-auto.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"規則剔除 {len(out)} 個")


if __name__ == "__main__":
    main()
