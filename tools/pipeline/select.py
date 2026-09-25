"""選字：候選詞條＋選字決定 → 依旅遊實用頻率排名、分級、分主題、切單元。韓文版。

輸入：build/candidates.json、build/curate/out-*.json（代理的去留決定）、build/curate/manual.json（人工覆寫，可無）
輸出：build/selection.json（排名後的卡片骨架）、build/ids.json（卡片編號登記，讓編號跨版本穩定；**不要刪**）
"""
import json, glob, os, re, sys, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import *
from themes import THEME_IDS, ASSIGN
from wordfreq import zipf_frequency

TARGET = int(os.environ.get("YH_TARGET", 1200))
TIER_SIZES = (0.25, 0.375)          # 必備 25%、常用 37.5%、其餘進階
UNIT_MAX, UNIT_MIN = 20, 4
THEME_FLOOR = int(os.environ.get("YH_THEME_FLOOR", 30))
# 2026-09-25 使用者：城市為主、濟州島可能自駕 → 自駕保留但縮小。
# 常用動詞與數字設上限：來源裡有一般學習詞表（90 Day 動詞表、國語院學習詞彙），會把一般動詞的收錄數灌高
#（不設上限時動詞 129 張、數字 130 張；日文版動詞只有 23 張），空出的名額依頻率給旅遊專題的字
THEME_CAP = {"DR": 20, "VB": 60, "NM": 100}
# 旅途核心情境的保底拉高（這些主題的字多半只被一份專題來源收錄，單看頻率會被料理、追星的字擠掉）
THEME_FLOOR_MAP = {"AP": 45, "TR": 40, "HT": 40, "RS": 40, "SH": 40, "LS": 40}
FAMILY = {t: fam for t, (fam, _) in ASSIGN.items()}   # 太小的主題組併到同家族裡最大的一組


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


def sort_key(it):
    return (-it["n"], -it["zipf"], it["head"])


def main():
    global by_id
    _, _, by_id = krdict()
    cands = {c["key"]: c for c in json.load(open(os.path.join(BUILD, "candidates.json"), encoding="utf-8"))}
    dec = load_decisions()
    missing = [k for k in cands if k not in dec]
    if missing:
        print(f"注意：{len(missing)} 個詞條還沒有選字決定（例：{missing[:5]}）")

    items, merges = {}, []
    for key, d in dec.items():
        if key not in cands:
            if d.get("keep") and d.get("added"):   # 人工補的詞（來源沒收到、但使用者指定的主題需要的字）
                cands[key] = {"key": key, "n": len(d.get("sources", [])), "sources": d.get("sources", []), "meanings": d.get("meanings", {}), "gloss": []}
                if key.startswith("w:") and key[2:] in by_id:      # 字典查得到的：帶入原形、唸法、漢字、英文對譯
                    e = by_id[key[2:]]
                    cands[key].update({"lemma": e["w"], "lemma_pron": e["pron1"], "origin": e["origin"], "pos": e["pos"], "gloss": e["en"][:6]})
            else:
                continue
        if d.get("keep"):
            th = d.get("theme")
            if th not in THEME_IDS:
                print("主題代碼錯誤", key, th)
                continue
            c = cands[key]
            items[key] = {"key": key, "head": re.sub(r"\s+", " ", d["head"].strip()), "kind": d.get("kind", "w"), "theme": th, "force": bool(d.get("force")),
                          "origin": d["origin"] if "origin" in d else c.get("origin", ""), "origin_set": "origin" in d,
                          "lemma": c.get("lemma", ""), "lemma_pron": c.get("lemma_pron", ""), "pos_kd": c.get("pos", ""),
                          "sources": set(c["sources"]), "fix": d.get("fix", ""),
                          "meanings": c.get("meanings", {}), "gloss": c.get("gloss", []), "keys": [key]}
        else:
            m = re.search(r"併入\s*([wp]:\S+)", d.get("why", ""))
            if m:
                merges.append((key, m.group(1)))
    for src, tgt in merges:
        if tgt in items and src in cands:
            items[tgt]["sources"] |= set(cands[src]["sources"])
            items[tgt]["keys"].append(src)
            for lang, v in cands[src].get("meanings", {}).items():
                items[tgt]["meanings"][lang] = list(dict.fromkeys(items[tgt]["meanings"].get(lang, []) + v))[:6]

    # 同寫法去重（不同批次的代理各自保留的）
    by_form = {}
    for it in items.values():
        fk = norm_key(it["head"]) + "|" + it["origin"]
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
        it["zipf"] = zipf_frequency(it["head"].replace("~", "").strip(), "ko")
    pool.sort(key=sort_key)
    print(f"保留 {len(pool)} 個（去重後），目標 {TARGET}")

    # 主題上限：超過的從該主題後段拿掉，空出的名額由其他主題依頻率遞補
    sel, cnt = [], collections.Counter()
    for it in pool:
        cap = THEME_CAP.get(it["theme"])
        if cap and cnt[it["theme"]] >= cap:
            continue
        sel.append(it)
        cnt[it["theme"]] += 1
        if len(sel) >= TARGET:
            break
    rest = [it for it in pool if it not in sel]
    # 主題保底：使用者要的主題（汗蒸幕、醫美、追星…）常只有少數專題文章收錄，單看收錄數會整批落榜；
    # 每個主題至少收 THEME_FLOOR 個（有上限的主題以上限為準），補進來的仍依頻率排在後段
    have = collections.Counter(it["theme"] for it in sel)
    floor = {th: min(THEME_FLOOR_MAP.get(th, THEME_FLOOR), THEME_CAP.get(th, 10 ** 6)) for th in THEME_IDS}
    extra = []
    for th in THEME_IDS:
        need = floor[th] - have[th]
        if need > 0:
            more = [it for it in rest if it["theme"] == th][:need]
            extra += more
            have[th] += len(more)
    if extra:
        drop, i = set(), len(sel) - 1
        while len(drop) < len(extra) and i >= 0:
            th = sel[i]["theme"]
            if have[th] > floor[th]:
                drop.add(i)
                have[th] -= 1
            i -= 1
        sel = [it for k, it in enumerate(sel) if k not in drop] + extra
        sel.sort(key=sort_key)
        print(f"主題保底補入 {len(extra)} 個：", collections.Counter(it["theme"] for it in extra).most_common())
    # 一定要收的字（manual.json 的 force：使用者指定的主題裡，來源都沒收到的關鍵字，例如 키오스크、택스 리펀드、원 플러스 원）
    forced = [it for it in pool if it.get("force") and it not in sel]
    if forced:
        drop, i = set(), len(sel) - 1
        while len(drop) < len(forced) and i >= 0:
            th = sel[i]["theme"]
            if not sel[i].get("force") and have[th] > floor[th]:
                drop.add(i)
                have[th] -= 1
            i -= 1
        sel = [it for k, it in enumerate(sel) if k not in drop] + forced
        for it in forced:
            have[it["theme"]] += 1
        sel.sort(key=sort_key)
        print(f"指定收錄 {len(forced)} 個：", [it["head"] for it in forced])
    short = {th: have[th] for th in THEME_IDS if have[th] < floor[th]}
    if short:
        print("保底仍不足的主題（候選不夠，要補來源）：", short)
    dist = collections.Counter(it["n"] for it in sel)
    print("入選的收錄數分佈:", sorted(dist.items(), reverse=True))

    # 分級
    n1 = round(len(sel) * TIER_SIZES[0])
    n2 = n1 + round(len(sel) * TIER_SIZES[1])
    for i, it in enumerate(sel):
        it["rank"] = i + 1
        it["tier"] = 1 if i < n1 else 2 if i < n2 else 3

    # 編號登記（跨版本穩定：音檔檔名、使用者的星號都掛在編號上）
    ids_path = os.path.join(BUILD, "ids.json")
    ids = json.load(open(ids_path)) if os.path.exists(ids_path) else {}
    nxt = max([int(v) for v in ids.values()] + [0]) + 1
    for it in sel:
        fk = f"{norm_key(it['head'])}|{it['origin']}"
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

    # 單元：級內依主題分組；過大切段、過小併入同家族最大組；課的順序依整組平均排名
    units = []
    for tier in (1, 2, 3):
        groups = collections.OrderedDict()
        for it in sel:
            if it["tier"] == tier:
                groups.setdefault(it["theme"], []).append(it)
        small = [th for th, g in groups.items() if len(g) < UNIT_MIN]
        for th in small:
            fam = [t for t in groups if t != th and FAMILY[t] == FAMILY[th] and len(groups[t]) >= UNIT_MIN]
            if not fam:
                # 同家族沒有別的組（店員廣播只有自己一個主題）：併進這條線的寒暄組，不要留一站只有一兩個字的課
                fam = [t for t in groups if t != th and FAMILY[t] == "basic" and len(groups[t]) >= UNIT_MIN]
            if fam:
                host = max(fam, key=lambda t: len(groups[t]))
                groups[host].extend(groups.pop(th))
                groups[host].sort(key=lambda it: it["rank"])
        order = sorted(groups.items(), key=lambda kv: sum(x["rank"] for x in kv[1]) / len(kv[1]))
        if tier == 1:
            # 必備線從打招呼開始（平均排名最前面的是購物，但初學者第一課應該是寒暄）
            order = [kv for kv in order if kv[0] == "GR"] + [kv for kv in order if kv[0] != "GR"]
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


if __name__ == "__main__":
    main()
