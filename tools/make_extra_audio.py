"""課程的音檔（2026-10-02，旅ことば的同名程式改成韓文版）：四十音課程。
讀一份或多份清單 [{"file": "audio/c/hon-3.mp3", "text": "さんぼん", "voice": "n", "rate": "-25%"}, …]
（由 tools/build_letters.py 寫到工作區 build/），用 edge-tts 合成、修剪前後靜音後存檔。
文字或語速沒變的檔案不重做（hash 記在工作區 build/extra-manifest.json）。

單一音節（아、가、까…）放慢 30%：2026-10-02 量過，SunHi 念「사」正常語速有聲段只有約 60ms，-40% 約 180ms。

用法：python tools/make_extra_audio.py [清單路徑…]（預設 build/letters_tts.json）"""
import asyncio, hashlib, json, os, subprocess, sys, tempfile
import edge_tts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get("YH_WORK", os.path.expanduser("~/Desktop/Claude code/workspace/work/ko-travel-vocab"))
MANIFEST = os.path.join(WORK, "build", "extra-manifest.json")
VOICES = {"f": "ko-KR-SunHiNeural", "m": "ko-KR-InJoonNeural"}
FFMPEG = "/opt/homebrew/bin/ffmpeg"
CONCURRENCY = 6


def trim(src, dst):
    """前面留 60ms、後面留 180ms 靜音，重新壓成 48kbps 單聲道 MP3"""
    af = ("silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.06,"
          "areverse,silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.18,areverse")
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", src, "-af", af, "-ac", "1", "-ar", "24000",
                    "-codec:a", "libmp3lame", "-b:a", "48k", dst], check=True)


async def synth(sem, job, stats):
    dst = os.path.join(ROOT, job["file"])
    async with sem:
        last = None
        for attempt in range(5):
            try:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    raw = tmp.name
                await edge_tts.Communicate(job["text"], VOICES[job.get("voice", "f")], rate=job.get("rate", "+0%")).save(raw)
                if os.path.getsize(raw) < 800:
                    raise RuntimeError("音檔太小")
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                await asyncio.to_thread(trim, raw, dst)
                os.unlink(raw)
                stats["ok"] += 1
                return True
            except Exception as e:   # 網路錯誤或被限流：退避重試
                last = e
                await asyncio.sleep(2 ** attempt)
        stats["fail"].append((job["file"], str(last)))
        return False


def sig(job):
    return hashlib.sha1(f'{job["text"]}|{job.get("voice", "f")}|{job.get("rate", "+0%")}'.encode()).hexdigest()[:16]


async def main(paths):
    jobs = []
    for p in paths:
        if os.path.exists(p):
            jobs += json.load(open(p, encoding="utf-8"))
    man = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    todo = [j for j in jobs if man.get(j["file"]) != sig(j) or not os.path.exists(os.path.join(ROOT, j["file"]))]
    print(f"清單 {len(jobs)} 個，要做 {len(todo)} 個", flush=True)
    sem = asyncio.Semaphore(CONCURRENCY)
    stats = {"ok": 0, "fail": []}
    done = 0
    for i in range(0, len(todo), 60):
        batch = todo[i:i + 60]
        res = await asyncio.gather(*(synth(sem, j, stats) for j in batch))
        for j, ok in zip(batch, res):
            if ok:
                man[j["file"]] = sig(j)
        done += len(batch)
        json.dump(man, open(MANIFEST, "w"), indent=0)
        print(f"{done}/{len(todo)}", flush=True)
    print(f"完成 {stats['ok']}，失敗 {len(stats['fail'])}", stats["fail"][:5])


if __name__ == "__main__":
    args = sys.argv[1:] or [os.path.join(WORK, "build", "letters_tts.json")]
    asyncio.run(main(args))
