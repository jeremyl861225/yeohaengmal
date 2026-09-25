"""選字批次：candidates.json → build/curate/in-NN.json（每批 YH_CURATE_BATCH 條，預設 120）。
已經有決定的 key（out-*.json、manual.json）不再切進去，所以可以重跑接續。"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD

BATCH = int(os.environ.get("YH_CURATE_BATCH", 150))
CUR = os.path.join(BUILD, "curate")


def main():
    cands = json.load(open(os.path.join(BUILD, "candidates.json"), encoding="utf-8"))
    done = set()
    for f in glob.glob(os.path.join(CUR, "out-*.json")) + glob.glob(os.path.join(CUR, "manual.json")):
        try:
            done |= {d["key"] for d in json.load(open(f, encoding="utf-8"))}
        except Exception as e:
            print("讀不了", f, e)
    # 已經派給代理、還在做的批次（YH_KEEP_IN="01,02"）：那些 key 也算已分配，不重複切
    for nn in filter(None, os.environ.get("YH_KEEP_IN", "").split(",")):
        done |= {d["key"] for d in json.load(open(os.path.join(CUR, f"in-{int(nn):02d}.json"), encoding="utf-8"))}
    todo = [c for c in cands if c["key"] not in done]
    # 優先順序：收錄數高的先；只被一份收錄的，字典查得到的詞先（基本難度優先），再來是短的詞組與句子
    lv = {"초급": 3, "중급": 2, "고급": 1}
    syl = lambda s: len(re.findall(r"[가-힣]", s))
    todo.sort(key=lambda c: (-c["n"], 0 if c["kind"] == "w" else 1, -lv.get(c.get("level", ""), 0),
                             syl(c["head"]) if c["kind"] == "p" else 0, -c["zipf"]))
    existing = [int(os.path.basename(p)[3:5]) for p in glob.glob(os.path.join(CUR, "in-*.json"))]
    nxt = max(existing + [0]) + 1
    rows = []
    for c in todo:
        rows.append({
            "key": c["key"], "n": c["n"], "zipf": round(c["zipf"], 2), "forms": c["forms"][:4], "head": c["head"],
            "lemma": c.get("lemma", ""), "origin": c.get("origin", ""), "level": c.get("level", ""), "kd_gloss": c.get("gloss", [])[:3],
            "src_meaning": {k: v[:4] for k, v in c["meanings"].items()}, "src_pron": c.get("src_pron", [])[:2],
            "sections": [s.split(":", 1)[1] for s in c["sections"][:5]],
        })
    made = []
    for i in range(0, len(rows), BATCH):
        name = os.path.join(CUR, f"in-{nxt:02d}.json")
        json.dump(rows[i:i + BATCH], open(name, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        made.append((os.path.basename(name), len(rows[i:i + BATCH])))
        nxt += 1
    print(f"待選 {len(rows)} 條 → {len(made)} 批：", made)


if __name__ == "__main__":
    main()
