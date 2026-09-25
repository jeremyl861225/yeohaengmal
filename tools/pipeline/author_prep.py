"""把選好的卡切成撰寫批次：build/author/in-NN.json（給撰寫代理）。已寫好的編號會跳過，可以重跑接續。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import *
from themes import theme_list

BATCH = int(os.environ.get("YH_BATCH", 100))


def main():
    sel = json.load(open(os.path.join(BUILD, "selection.json"), encoding="utf-8"))
    names = {t["id"]: t["name"] for t in theme_list()}
    outdir = os.path.join(BUILD, "author")
    os.makedirs(outdir, exist_ok=True)
    done = set()
    for f in os.listdir(outdir):
        if f.startswith("out-") and f.endswith(".json"):
            for d in json.load(open(os.path.join(outdir, f), encoding="utf-8")):
                if d.get("ex") or d.get("zh") or d.get("drop"):
                    done.add(d["id"])
    todo = [c for c in sel["cards"] if c["id"] not in done]
    todo.sort(key=lambda c: c["id"])
    existing = [int(f[3:5]) for f in os.listdir(outdir) if f.startswith("in-") and f.endswith(".json")]
    start = max(existing + [0]) + 1
    for i in range(0, len(todo), BATCH):
        part = []
        for c in todo[i:i + BATCH]:
            d = {"id": c["id"], "head": c["head"], "kind": c["kind"], "theme": names[c["theme"]]}
            if c.get("origin"):
                d["origin"] = c["origin"]
            m = {k: v[:3] for k, v in c.get("meanings", {}).items() if v}
            if m:
                d["src_meaning"] = m
            if c.get("gloss"):
                d["kd_gloss"] = c["gloss"][:4]
            part.append(d)
        n = start + i // BATCH
        json.dump(part, open(os.path.join(outdir, f"in-{n:02d}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"in-{n:02d}.json", len(part))
    print(f"待撰寫 {len(todo)}，已完成 {len(done)}")


if __name__ == "__main__":
    main()
