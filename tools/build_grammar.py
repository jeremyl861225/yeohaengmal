"""文法專欄資料（2026-10-03）：tools/grammar/{a,c,d,e,f}.py（內容手寫）→ data/grammar.json，並列出要合成的音檔。

輸出
- data/grammar.json：{ title, intro, groups: [{ title, lessons: [{ id, title, sub, summary, formula[], body[], table, ex[], notes[], quiz[] }] }] }
  - body／notes 的 **粗體** 與韓文字由 js/grammar.js 轉成標記；ex[].ko 裡的 [ ] 是要醒目標出的文法部分（朗讀時拿掉）。
  - ex[]：{ ko, zh, a }；a 是音檔 key（audio/<a>.mp3）。
  - quiz[]：{ s, zh, o[], a, why, au }：s 有 ___ 是填空題（o 是選項，a 是正解的位置）；s 是 null 是「選出正確的句子」（o 是整句）。au 是正解整句的音檔 key。
- workspace/build/grammar_tts.json：給 tools/make_extra_audio.py 的音檔清單（女聲 SunHi，語速 -10%）。
- 音檔名是「朗讀文字＋聲音＋語速」的雜湊（audio/g/<10 碼>.mp3）：句子改了網址就變，手機快取的舊檔不會播錯句子。沒用到的舊檔會被刪掉。

用法：python tools/build_grammar.py（工作區 .venv）；之後 python tools/make_extra_audio.py build/grammar_tts.json（只做新增或改過的）。
朗讀文字一律寫韓文字（數字也是），不放阿拉伯數字或英文字母：語音會把拉丁字母丟掉、數字念法也不一定對。"""
import datetime, glob, hashlib, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get("YH_WORK", os.path.expanduser("~/Desktop/Claude code/workspace/work/ko-travel-vocab"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grammar.a import GROUP_A, GROUP_B   # noqa: E402
from grammar.c import GROUP_C            # noqa: E402
from grammar.d import GROUP_D            # noqa: E402
from grammar.f import GROUP_F            # noqa: E402
from grammar.e import GROUP_E            # noqa: E402

VOICE, RATE = "f", "-10%"
KO_OK = re.compile(r"[가-힣 .,?!]+")
errors = []
tts = {}      # 音檔 key -> 朗讀文字


def err(lid, msg):
    errors.append(f"[{lid}] {msg}")


# 語音沒有套用的音變，朗讀時改送實際唸法（2026-10-03 聲紋比對：몇 명 被念成 [몃 명]，標準是 [면 명]）
SAY_FIX = {"몇 명이에요?": "면 명이에요?"}


def say(text):
    """朗讀文字 → 音檔 key"""
    text = SAY_FIX.get(text, text)
    key = "g/" + hashlib.sha1(f"{text}|{VOICE}|{RATE}".encode()).hexdigest()[:10]
    tts[key] = text
    return key


def plain(ko):
    return ko.replace("[", "").replace("]", "")


def lesson_out(l):
    lid = l["id"]
    if not re.fullmatch(r"\w+", lid):
        err(lid, "id 只能用字母數字底線")
    for k in ("title", "sub", "summary", "formula", "body", "ex", "notes", "quiz"):
        if not l.get(k):
            err(lid, f"缺 {k}")
    t = l.get("table")
    if t:
        head, rows = t
        for r in rows:
            if len(r) != len(head):
                err(lid, f"表格欄數不符：{r}")
    ex = []
    for ko, zh in l["ex"]:
        if ko.count("[") != ko.count("]") or ko.count("[") < 1:
            err(lid, f"例句的 [ ] 沒成對或沒標出重點：{ko}")
        if not KO_OK.fullmatch(plain(ko)):
            err(lid, f"例句含韓文字以外的字元：{ko}")
        if not zh:
            err(lid, f"例句缺中文：{ko}")
        ex.append({"ko": ko, "zh": zh, "a": say(plain(ko))})
    if len(ex) < 5 or len({e["zh"] for e in ex}) != len(ex):
        err(lid, "例句至少 5 句，中文不能重複（聽力題要用）")
    quiz = []
    for s, zh, opts, a, why in l["quiz"]:
        if not (2 <= len(opts) <= 4) or len(set(opts)) != len(opts):
            err(lid, f"選項要 2–4 個、不重複：{opts}")
        if not (0 <= a < len(opts)):
            err(lid, f"正解位置不對：{opts}")
        if not zh or not why:
            err(lid, f"題目缺中文或解釋：{opts}")
        if s is None:
            full = opts[a]
            for o in opts:
                if not KO_OK.fullmatch(o) or not o.endswith((".", "?", "!")):
                    err(lid, f"整句選項要韓文字加句尾標點：{o}")
        else:
            if s.count("___") != 1:
                err(lid, f"填空題要剛好一個 ___：{s}")
            full = s.replace("___", opts[a])
            if len({s.replace("___", o) for o in opts}) != len(opts):
                err(lid, f"填空後有重複的句子：{s}")
        if not KO_OK.fullmatch(full):
            err(lid, f"題目含韓文字以外的字元：{full}")
        quiz.append({"s": s, "zh": zh, "o": opts, "a": a, "why": why, "au": say(full)})
    if len(quiz) < 5:
        err(lid, "練習題至少 5 題")
    return {"id": lid, "title": l["title"], "sub": l["sub"], "summary": l["summary"], "formula": l["formula"], "body": l["body"],
            "table": ({"head": t[0], "rows": t[1]} if t else None), "ex": ex, "notes": l["notes"], "quiz": quiz}


def main():
    groups = []
    ids = set()
    for g in (GROUP_A, GROUP_B, GROUP_C, GROUP_F, GROUP_D, GROUP_E):
        out = {"title": g["title"], "lessons": []}
        for l in g["lessons"]:
            if l["id"] in ids:
                err(l["id"], "id 重複")
            ids.add(l["id"])
            out["lessons"].append(lesson_out(l))
        groups.append(out)
    if errors:
        print("\n".join(errors))
        sys.exit(f"{len(errors)} 個問題，沒有輸出")
    n = sum(len(g["lessons"]) for g in groups)
    data = {
        "version": datetime.date.today().isoformat(), "lang": "ko", "title": "文法",
        "intro": f"從語序、助詞、動詞變化（含不規則變化）到旅行最常用的句型，共 {n} 課。每課先看重點與例句（點一下就能聽），再做練習；答對八成算學完。",
        "groups": groups,
    }
    with open(os.path.join(ROOT, "data", "grammar.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    jobs = [{"file": f"audio/{k}.mp3", "text": t, "voice": VOICE, "rate": RATE} for k, t in sorted(tts.items())]
    os.makedirs(os.path.join(WORK, "build"), exist_ok=True)
    with open(os.path.join(WORK, "build", "grammar_tts.json"), "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=0)
    keep = {os.path.basename(j["file"]) for j in jobs}
    gone = [p for p in glob.glob(os.path.join(ROOT, "audio", "g", "*.mp3")) if os.path.basename(p) not in keep]
    for p in gone:
        os.remove(p)
    print(f"{n} 課、例句 {sum(len(l['ex']) for g in groups for l in g['lessons'])} 句、練習題 {sum(len(l['quiz']) for g in groups for l in g['lessons'])} 題；"
          f"音檔 {len(jobs)} 個（刪掉舊的 {len(gone)} 個）；data/grammar.json {os.path.getsize(os.path.join(ROOT, 'data', 'grammar.json')) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
