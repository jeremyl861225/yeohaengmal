"""規則補完：選字代理停擺時，用規則替剩下的候選做決定（每條加 "auto": true，撰寫階段的代理會再核一次）。
用法：python auto_curate.py in-07.json [in-08.json …]  → 寫 build/curate/out-07.json …（已存在的 out 檔會接著補沒做完的條目）

主題：先看來源的 theme_hint（只標一個主題的專題來源最可靠），再看小標題關鍵字；都判不出來就依 KRDict 語義分類，最後放 GR。
刪除：沒有韓文、助詞語尾、20 個音節以上的長句（店員廣播的短句保留）。"""
import glob, json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

CUR = os.path.join(BUILD, "curate")
SECTION_RULES = [
    ("KP", r"追星|演唱會|應援|偶像|K-?pop|콘서트|응원|아이돌|팬|굿즈|concert|idol"),
    ("HB", r"韓服|拍照|打卡|自拍|한복|사진|photo"),
    ("DM", r"醫美|皮膚科|療程|雷射|시술|피부과|레이저|성형|lifting|laser"),
    ("ON", r"汗蒸|澡堂|搓澡|三溫暖|찜질|목욕|사우나|sauna|jjimjil"),
    ("BB", r"烤肉|部位|五花|炸雞|치킨|고기|삼겹|갈비|BBQ|barbecue|chicken"),
    ("DK", r"咖啡|點餐機|甜點|飲料|카페|커피|키오스크|음료|디저트|cafe|coffee|kiosk|dessert|drink"),
    ("DS", r"美妝|保養|化妝|膚質|화장품|스킨|로션|피부 타입|cosmetic|skin ?care|beauty"),
    ("CV", r"便利商店|超商|편의점|convenience"),
    ("SH", r"購物|結帳|退稅|試穿|尺寸|쇼핑|계산|택스|면세|사이즈|shopping|tax ?refund|size"),
    ("RS", r"餐廳|點餐|外帶|外送|식당|주문|포장|배달|restaurant|order"),
    ("FD", r"料理|食材|菜單|음식|요리|메뉴|food|dish|menu"),
    ("MD", r"看病|醫院|症狀|藥局|身體|병원|약국|증상|doctor|hospital|pharmacy|symptom|body"),
    ("EM", r"緊急|求助|報警|遺失|警察|긴급|경찰|분실|emergency|police|lost"),
    ("AP", r"機場|入境|海關|登機|機上|行李|공항|입국|세관|탑승|기내|airport|immigration|customs|flight"),
    ("TR", r"地鐵|捷運|交通卡|轉乘|KTX|지하철|교통카드|환승|subway|metro|train|t-?money"),
    ("BT", r"巴士|公車|計程車|叫車|버스|택시|bus|taxi"),
    ("DR", r"自駕|租車|加油|停車|운전|주유|렌터카|주차|driv|rental car|gas station|parking"),
    ("DI", r"問路|方向|方位|길|방향|direction|way"),
    ("HT", r"住宿|飯店|民宿|入住|退房|호텔|숙소|체크|hotel|accommodation|check"),
    ("SG", r"觀光|景點|門票|宮|市場|관광|입장|궁|시장|sightseeing|ticket|palace"),
    ("SN", r"標示|招牌|告示|표지|안내판|sign"),
    ("SV", r"網路|Wi-?Fi|換錢|ATM|天氣|手機|郵局|와이파이|환전|날씨|우체국|internet|weather|money|atm"),
    ("LS", r"店員|廣播|站務|안내방송|직원|announcement|staff"),
    ("NM", r"數字|數量|時間|日期|價錢|숫자|시간|날짜|가격|number|time|date|price"),
    ("VB", r"動詞|形容詞|동사|형용사|verb|adjective"),
    ("GR", r"寒暄|問候|招呼|基本|會話|인사|기본|greeting|basic|essential"),
]


def source_hints():
    hints = {}
    for f in glob.glob(os.path.join(SOURCES, "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        hints[d["id"]] = d.get("theme_hint", [])
    return hints


def theme_for(c, hints, cand):
    votes = collections.Counter()
    for s in cand.get("sources", []):
        h = hints.get(s, [])
        if len(h) == 1:
            votes[h[0]] += 2
    text = " ".join(c.get("sections", [])) + " " + " ".join(sum(c.get("src_meaning", {}).values(), []))
    for th, pat in SECTION_RULES:
        if re.search(pat, text, re.I):
            votes[th] += 1
            break
    if votes:
        return votes.most_common(1)[0][0]
    return "GR"


def decide(c, hints, cands):
    cand = cands.get(c["key"], {})
    head = c["head"]
    syl = len(re.findall(r"[가-힣]", head))
    if not has_hangul(head):
        return {"key": c["key"], "keep": False, "why": "沒有韓文", "auto": True}
    if cand.get("pos") in ("조사", "어미"):
        return {"key": c["key"], "keep": False, "why": "助詞或語尾", "auto": True}
    th = theme_for(c, hints, cand)
    kind = "p" if c["key"].startswith("p:") and (" " in head or re.search(r"[?.!]$", head)) else "w"
    if kind == "p" and syl > 20 and th != "LS":
        return {"key": c["key"], "keep": False, "why": "旅客說的長句", "auto": True}
    if kind == "p" and syl > 28:
        return {"key": c["key"], "keep": False, "why": "很長的廣播全文", "auto": True}
    return {"key": c["key"], "keep": True, "head": head, "kind": kind, "theme": th, "auto": True}


def main():
    hints = source_hints()
    cands = {c["key"]: c for c in json.load(open(os.path.join(BUILD, "candidates.json"), encoding="utf-8"))}
    for name in sys.argv[1:]:
        src = os.path.join(CUR, os.path.basename(name))
        dst = src.replace("in-", "out-")
        rows = json.load(open(src, encoding="utf-8"))
        have = json.load(open(dst, encoding="utf-8")) if os.path.exists(dst) else []
        done = {d["key"] for d in have}
        add = [decide(c, hints, cands) for c in rows if c["key"] not in done]
        # 保持與輸入同順序
        byk = {d["key"]: d for d in have + add}
        out = [byk[c["key"]] for c in rows]
        json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(os.path.basename(dst), f"代理已做 {len(have)}，規則補 {len(add)}")


if __name__ == "__main__":
    main()
