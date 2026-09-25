"""選字：候選詞條＋選字決定 → 依旅遊實用頻率排名、分級、分主題、切單元。

輸入：build/candidates.json、build/curate/out-*.json（代理的去留決定）、build/curate/manual.json（人工覆寫，可無）
輸出：build/selection.json（排名後的 1200 張卡骨架）、build/ids.json（卡片編號登記，讓編號跨版本穩定）
"""
import json, glob, os, re, sys, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import *
from themes import THEME_IDS
from wordfreq import zipf_frequency

TARGET = int(os.environ.get("TK_TARGET", 1200))
TIER_SIZES = (0.25, 0.375)          # 必備 25%、常用 37.5%、其餘進階
UNIT_MAX, UNIT_MIN = 20, 4
THEME_FLOOR = int(os.environ.get("TK_THEME_FLOOR", 30))
FAMILY = {  # 太小的主題組併到同家族裡最大的一組
    "GR": "basic", "VB": "basic", "NM": "basic",
    "AP": "move", "TR": "move", "BT": "move", "DR": "move", "DI": "move",
    "HT": "stay", "ON": "stay",
    "RS": "food", "FD": "food", "DK": "food",
    "SH": "shop", "CV": "shop", "DS": "shop",
    "MD": "care", "EM": "care",
    "SG": "city", "SN": "city", "SV": "city",
    "LS": "listen",
}


def load_decisions():
    dec = {}
    for f in sorted(glob.glob(os.path.join(BUILD, "curate", "out-*.json"))):
        for d in json.load(open(f, encoding="utf-8")):
            dec[d["key"]] = d
    man = os.path.join(BUILD, "curate", "manual.json")
    if os.path.exists(man):
        for d in json.load(open(man, encoding="utf-8")):
            dec[d["key"]] = {**dec.get(d["key"], {}), **d}
    return dec


def main():
    cands = {c["key"]: c for c in json.load(open(os.path.join(BUILD, "candidates.json"), encoding="utf-8"))}
    dec = load_decisions()
    missing = [k for k in cands if k not in dec]
    if missing:
        print(f"注意：{len(missing)} 個詞條還沒有選字決定（例：{missing[:5]}）")

    items = {}
    merges = []
    for key, d in dec.items():
        if key not in cands:
            if d.get("keep") and d.get("added"):   # 人工補的詞：來源段落有整組列出、但抽取只抓到部分（例如日期 1～10 日）
                cands[key] = {"key": key, "n": len(d.get("sources", [])), "sources": d.get("sources", []), "meanings": d.get("meanings", {}), "gloss": []}
            else:
                continue
        if d.get("keep"):
            th = d.get("theme")
            if th not in THEME_IDS:
                print("主題代碼錯誤", key, th)
                continue
            items[key] = {"key": key, "head": d["head"].strip(), "reading": d["reading"].strip(), "kind": d.get("kind", "w"),
                          "theme": th, "sources": set(cands[key]["sources"]), "fix": d.get("fix", ""),
                          "meanings": cands[key].get("meanings", {}), "gloss": cands[key].get("gloss", []), "keys": [key]}
        else:
            m = re.search(r"併入\s*([wp]:\S+)", d.get("why", ""))
            if m:
                merges.append((key, m.group(1)))
    for src, tgt in merges:
        if tgt in items and src in cands:
            items[tgt]["sources"] |= set(cands[src]["sources"])
            items[tgt]["keys"].append(src)
            for lang, v in cands[src].get("meanings", {}).items():
                items[tgt]["meanings"].setdefault(lang, [])
                items[tgt]["meanings"][lang] = list(dict.fromkeys(items[tgt]["meanings"][lang] + v))[:6]

    # 同寫法同讀音去重（不同分段的代理各自保留的）
    by_form = {}
    for it in items.values():
        fk = (it["head"], kata2hira(it["reading"]))
        if fk in by_form:
            a = by_form[fk]
            a["sources"] |= it["sources"]
            a["keys"] += it["keys"]
            for lang, v in it["meanings"].items():
                a["meanings"][lang] = list(dict.fromkeys(a["meanings"].get(lang, []) + v))[:6]
        else:
            by_form[fk] = it
    pool = list(by_form.values())
    for it in pool:
        it["n"] = len(it["sources"])
        it["zipf"] = zipf_frequency(it["head"].replace("〜", ""), "ja")
    pool.sort(key=lambda it: (-it["n"], -it["zipf"], it["reading"]))
    print(f"保留 {len(pool)} 個（去重後），目標 {TARGET}")
    sel = pool[:TARGET]
    # 主題保底：使用者指定要的主題（自駕、溫泉、藥妝…）常只有少數專題文章收錄，
    # 單看收錄數會整批落榜；每個主題至少收 THEME_FLOOR 個（不足就全收），補進來的仍依頻率排在後段
    have = collections.Counter(it["theme"] for it in sel)
    extra = []
    for th in THEME_IDS:
        need = THEME_FLOOR - have[th]
        if need > 0:
            more = [it for it in pool[TARGET:] if it["theme"] == th][:need]
            extra += more
            have[th] += len(more)
    if extra:
        drop, i = [], len(sel) - 1
        while len(drop) < len(extra) and i >= 0:
            th = sel[i]["theme"]
            if have[th] > THEME_FLOOR:
                drop.append(i)
                have[th] -= 1
            i -= 1
        sel = [it for k, it in enumerate(sel) if k not in set(drop)] + extra
        sel.sort(key=lambda it: (-it["n"], -it["zipf"], it["reading"]))
        print(f"主題保底補入 {len(extra)} 個：", collections.Counter(it["theme"] for it in extra).most_common())
    dist = collections.Counter(it["n"] for it in sel)
    print("入選的收錄數分佈:", sorted(dist.items(), reverse=True))

    # 分級
    n1 = round(len(sel) * TIER_SIZES[0])
    n2 = n1 + round(len(sel) * TIER_SIZES[1])
    for i, it in enumerate(sel):
        it["rank"] = i + 1
        it["tier"] = 1 if i < n1 else 2 if i < n2 else 3

    # 編號登記（跨版本穩定）
    ids_path = os.path.join(BUILD, "ids.json")
    ids = json.load(open(ids_path)) if os.path.exists(ids_path) else {}
    nxt = max([int(v) for v in ids.values()] + [0]) + 1
    for it in sel:
        fk = f"{it['head']}|{kata2hira(it['reading'])}"
        if fk not in ids:
            ids[fk] = f"{nxt:04d}"
            nxt += 1
        it["id"] = ids[fk]
    json.dump(ids, open(ids_path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

    # 站號：同主題依排名 01, 02…
    cnt = collections.Counter()
    for it in sel:
        cnt[it["theme"]] += 1
        it["no"] = cnt[it["theme"]]

    # 單元：級內依主題分組，主題依該組最高排名排序；過大切段、過小併入同家族最大組
    units = []
    for tier in (1, 2, 3):
        groups = collections.OrderedDict()
        for it in sel:
            if it["tier"] == tier:
                groups.setdefault(it["theme"], []).append(it)
        small = [th for th, g in groups.items() if len(g) < UNIT_MIN]
        for th in small:
            fam = [t for t in groups if t != th and FAMILY[t] == FAMILY[th] and len(groups[t]) >= UNIT_MIN]
            if fam:
                host = max(fam, key=lambda t: len(groups[t]))
                groups[host].extend(groups.pop(th))
                groups[host].sort(key=lambda it: it["rank"])
        # 課的順序：整組的平均排名（比單看第一名穩定，必備線才不會從招牌開始）
        order = sorted(groups.items(), key=lambda kv: sum(x["rank"] for x in kv[1]) / len(kv[1]))
        for th, g in order:
            k = math.ceil(len(g) / UNIT_MAX)
            size = math.ceil(len(g) / k)
            for p in range(k):
                part = g[p * size:(p + 1) * size]
                if not part:
                    continue
                own = [x["no"] for x in part if x["theme"] == th]
                units.append({"id": f"{tier}-{th}-{p + 1}", "t": tier, "th": th, "part": p + 1, "parts": k,
                              "cards": [x["id"] for x in part],
                              "from": min(own) if own else part[0]["no"], "to": max(own) if own else part[-1]["no"]})
    out = [{k: (sorted(v) if isinstance(v, set) else v) for k, v in it.items()} for it in sel]
    json.dump({"cards": out, "units": units}, open(os.path.join(BUILD, "selection.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tiers = collections.Counter(it["tier"] for it in sel)
    print("分級:", dict(tiers), " 單元數:", len(units))
    print("主題分佈:", collections.Counter(it["theme"] for it in sel).most_common())
    print("各級單元大小:", [(u["id"], len(u["cards"])) for u in units][:80])


if __name__ == "__main__":
    main()
