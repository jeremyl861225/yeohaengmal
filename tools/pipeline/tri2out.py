"""快速分流的結果 tri-NN.tsv → out-NN.json（每條加 "auto": "triage"，head 沿用候選的代表寫法，撰寫階段再修）。
用法：python tri2out.py 16 17 …（批號）"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import BUILD
from themes import THEME_IDS

CUR = os.path.join(BUILD, "curate")


def main():
    for no in sys.argv[1:]:
        nn = f"{int(no):02d}"
        rows = json.load(open(os.path.join(CUR, f"in-{nn}.json"), encoding="utf-8"))
        tri = {}
        for line in open(os.path.join(CUR, f"tri-{nn}.tsv"), encoding="utf-8"):
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2 and parts[0]:
                tri[parts[0]] = parts
        out, missing = [], 0
        for c in rows:
            p = tri.get(c["key"])
            if not p:
                missing += 1
                continue
            if p[1] == "K" and len(p) >= 3 and p[2] in THEME_IDS:
                kind = p[3] if len(p) >= 4 and p[3] in ("w", "p") else ("p" if " " in c["head"] else "w")
                out.append({"key": c["key"], "keep": True, "head": c["head"], "kind": kind, "theme": p[2], "auto": "triage"})
            else:
                out.append({"key": c["key"], "keep": False, "why": "快速分流刪除", "auto": "triage"})
        json.dump(out, open(os.path.join(CUR, f"out-{nn}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"out-{nn}.json：留 {sum(1 for o in out if o['keep'])}、刪 {sum(1 for o in out if not o['keep'])}、缺 {missing}")


if __name__ == "__main__":
    main()
