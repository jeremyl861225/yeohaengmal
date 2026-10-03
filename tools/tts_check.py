"""韓文發音檢查（2026-10-03，仿旅ことば的 tools/tts_check.py）：語音有沒有照卡上顯示的「實際唸法」r 念。

把每張「唸法跟寫法不同」的單字卡，用卡上的唸法 r（連音、鼻音化、硬音化已套用）以同一個聲音另合成一份，
跟現有音檔（送的是原寫法）比聲紋（MFCC＋DTW）：念法一樣距離小，語音沒套用音變或漏念字，距離大。

用法（工作區 .venv，要有 edge-tts、numpy）：
  python tools/tts_check.py synth   # 合成 r 版到 workspace/build/ttscheck/{f,m}/<id>.mp3（可中斷續跑）
  python tools/tts_check.py score   # 比對，寫 build/ttscheck/scores.json（距離由大到小）
判讀（2026-10-03 的 271 張）：中位數 0.4；< 4 ＝念法一樣（228 張）；4–9 ＝多半只差語調（40 張）；12 以上要逐條查（3 張，都是真問題）。
負對照（拿別張卡的音檔比）最小 9.3、中位數 21，所以 9–12 之間要人聽。
抓到的毛病與處理寫在 build_data.py 的 FIX_PRON（語音會丟掉拉丁字母、阿拉伯數字念法跟自動唸法不同）。
限制：
  • 只比「唸法≠寫法」的單字；唸法＝寫法的 857 個單字、2,400 句例句沒有標準答案可比（例句裡的數字另外用漢數詞拼法比過，都對）。
  • 四十音的單音節不能用這個比：男女聲音色差太大，61 選 1 只認對 13 個。要驗證得靠語音辨識或人聽。
  • 距離只告訴你「兩份念得像不像」，不知道誰對；12 以上的都要看是哪邊錯。"""
import asyncio, json, os, re, subprocess, sys, tempfile
import numpy as np

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get("YH_WORK", os.path.expanduser("~/Desktop/Claude code/workspace/work/ko-travel-vocab"))
HERE = os.path.join(WORK, "build", "ttscheck")
FFMPEG = "/opt/homebrew/bin/ffmpeg"
VOICES = {"f": "ko-KR-SunHiNeural", "m": "ko-KR-InJoonNeural"}


def targets():
    cards = json.load(open(os.path.join(APP, "data", "cards.json"), encoding="utf-8"))["cards"]
    tts = json.load(open(os.path.join(WORK, "build", "tts.json"), encoding="utf-8"))
    out = {}
    for c in cards:
        said, shown = tts[c["id"]]["w"], c["r"]
        if re.sub(r"\s", "", said) != re.sub(r"\s", "", shown) and re.fullmatch(r"[가-힣 ]+", shown):
            out[c["id"]] = {"said": said, "r": shown, "w": c["w"], "zh": c["zh"]}
    return out


def trim(src, dst):
    af = ("silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.06,"
          "areverse,silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.18,areverse")
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", src, "-af", af, "-ac", "1", "-ar", "24000",
                    "-codec:a", "libmp3lame", "-b:a", "48k", dst], check=True)


async def synth_one(sem, voice, text, dst, stats):
    import edge_tts
    async with sem:
        last = None
        for attempt in range(5):
            try:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    raw = tmp.name
                await edge_tts.Communicate(text, VOICES[voice]).save(raw)
                if os.path.getsize(raw) < 800:
                    raise RuntimeError("音檔太小")
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                await asyncio.to_thread(trim, raw, dst)
                os.unlink(raw)
                stats["ok"] += 1
                return
            except Exception as e:
                last = e
                await asyncio.sleep(2 ** attempt)
        stats["fail"].append((dst, str(last)))


async def synth():
    sem = asyncio.Semaphore(8)
    stats = {"ok": 0, "fail": []}
    jobs = [synth_one(sem, v, t["r"], os.path.join(HERE, v, f"{cid}.mp3"), stats)
            for cid, t in targets().items() for v in VOICES if not os.path.exists(os.path.join(HERE, v, f"{cid}.mp3"))]
    print(f"要合成 {len(jobs)} 個", flush=True)
    for i in range(0, len(jobs), 80):
        await asyncio.gather(*jobs[i:i + 80])
        print(f"  {min(i + 80, len(jobs))}/{len(jobs)}", flush=True)
    print("完成", stats["ok"], "失敗", len(stats["fail"]), stats["fail"][:5])


# ---------- 聲紋比對（和 tabi-kotoba/tools/tts_check.py 同一套，語言無關）----------
SR, NFFT, HOP, WIN = 16000, 512, 160, 400


def pcm(path):
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def mel_bank(n=26):
    mel = lambda f: 2595 * np.log10(1 + f / 700)
    imel = lambda m: 700 * (10 ** (m / 2595) - 1)
    pts = imel(np.linspace(mel(60), mel(7600), n + 2))
    bins = np.floor((NFFT + 1) * pts / SR).astype(int)
    fb = np.zeros((n, NFFT // 2 + 1))
    for i in range(1, n + 1):
        l, c, r = bins[i - 1], bins[i], bins[i + 1]
        fb[i - 1, l:c] = (np.arange(l, c) - l) / max(c - l, 1)
        fb[i - 1, c:r] = (r - np.arange(c, r)) / max(r - c, 1)
    return fb


FB = mel_bank()
DCT = np.cos(np.pi / 26 * (np.arange(26)[None, :] + 0.5) * np.arange(1, 13)[:, None])


def mfcc(x):
    x = np.append(x[0], x[1:] - 0.97 * x[:-1])
    if len(x) < WIN:
        x = np.pad(x, (0, WIN - len(x)))
    n = 1 + (len(x) - WIN) // HOP
    idx = np.arange(WIN)[None, :] + HOP * np.arange(n)[:, None]
    frames = x[idx] * np.hamming(WIN)
    pw = np.abs(np.fft.rfft(frames, NFFT)) ** 2 / NFFT
    e = np.log(pw @ FB.T + 1e-10)
    keep = e.max(axis=1) > e.max() - 9
    c = (e[keep] if keep.sum() > 5 else e) @ DCT.T
    return c - c.mean(axis=0)


def dtw(a, b):
    d = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(-1))
    n, m = d.shape
    acc = np.full((n + 1, m + 1), np.inf)
    acc[0, 0] = 0
    for i in range(1, n + 1):
        row, prev, di = acc[i], acc[i - 1], d[i - 1]
        best = np.minimum(prev[:-1], prev[1:]) + di
        for j in range(1, m + 1):
            v = best[j - 1]
            if row[j - 1] + di[j - 1] < v:
                v = row[j - 1] + di[j - 1]
            row[j] = v
    return acc[n, m] / (n + m)


def score():
    out = []
    for k, (cid, t) in enumerate(targets().items()):
        rec = {"id": cid, **t}
        for v in VOICES:
            a, b = os.path.join(APP, "audio", v, f"{cid}.mp3"), os.path.join(HERE, v, f"{cid}.mp3")
            if os.path.exists(a) and os.path.exists(b):
                rec[v] = round(float(dtw(mfcc(pcm(a)), mfcc(pcm(b)))), 2)
        out.append(rec)
        if k % 100 == 0:
            print(k, flush=True)
    out.sort(key=lambda r: -max(r.get("f", 0), r.get("m", 0)))
    json.dump(out, open(os.path.join(HERE, "scores.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("寫好", len(out), "；前 10 名：")
    for r in out[:10]:
        print(r["id"], r["w"], "→", r["r"], "| 送出", r["said"], "| f", r.get("f"), "m", r.get("m"))


if __name__ == "__main__":
    asyncio.run(synth()) if sys.argv[1:] == ["synth"] else score()
