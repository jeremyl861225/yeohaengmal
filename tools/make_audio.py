"""產生發音音檔：每張卡的單字與例句，女聲（f）與男聲（m）各一份。

讀 workspace/build/tts.json（{id: {"w": 單字朗讀文字, "x": 例句朗讀文字}}，由 build_data.py 產生），
輸出 audio/f/<id>.mp3、audio/f/<id>x.mp3、audio/m/…。
朗讀文字沒變的檔案不重做（hash 記在 build/tts-manifest.json）。產生後修剪前後靜音再存。
語音來源：Microsoft Edge 朗讀服務（edge-tts，非官方管道），僅供個人學習。
"""
import asyncio, hashlib, json, os, subprocess, sys, tempfile
import edge_tts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get("YH_WORK", os.path.expanduser("~/Desktop/Claude code/workspace/work/ko-travel-vocab"))
TTS = os.environ.get("YH_TTS", os.path.join(WORK, "build", "tts.json"))
MANIFEST = os.path.join(WORK, "build", "tts-manifest.json")
# 2026-09-25 暫定 SunHi＋InJoon（韓文只有 SunHi 一個女聲）；使用者試聽後若改 Hyunsu，換掉 m 並刪 tts-manifest 裡 audio/m 的紀錄重跑
VOICES = {"f": "ko-KR-SunHiNeural", "m": "ko-KR-InJoonNeural"}
FFMPEG = "/opt/homebrew/bin/ffmpeg"
CONCURRENCY = 6


def trim(src, dst):
    """前面留 60ms、後面留 180ms 靜音，重新壓成 48kbps 單聲道 MP3"""
    af = ("silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.06,"
          "areverse,silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.18,areverse")
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", src, "-af", af, "-ac", "1", "-ar", "24000",
                    "-codec:a", "libmp3lame", "-b:a", "48k", dst], check=True)


async def synth(sem, voice, text, dst, stats):
    async with sem:
        for attempt in range(5):
            try:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    raw = tmp.name
                await edge_tts.Communicate(text, VOICES[voice]).save(raw)
                if os.path.getsize(raw) < 800:
                    raise RuntimeError("音檔太小")
                await asyncio.to_thread(trim, raw, dst)
                os.unlink(raw)
                stats["ok"] += 1
                return True
            except Exception as e:  # 網路錯誤或被限流：退避重試
                await asyncio.sleep(2 ** attempt)
                last = e
        stats["fail"].append((dst, str(last)))
        return False


async def main(only=None):
    tts = json.load(open(TTS, encoding="utf-8"))
    man = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    sem = asyncio.Semaphore(CONCURRENCY)
    stats = {"ok": 0, "fail": []}
    jobs = []
    for cid, parts in tts.items():
        if only and cid not in only:
            continue
        for part, text in parts.items():
            if not text:
                continue
            for v in VOICES:
                rel = f"audio/{v}/{cid}{'x' if part == 'x' else ''}.mp3"
                dst = os.path.join(ROOT, rel)
                h = hashlib.sha1(f"{VOICES[v]}|{text}".encode()).hexdigest()[:16]
                if man.get(rel) == h and os.path.exists(dst):
                    continue
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                jobs.append((rel, h, synth(sem, v, text, dst, stats)))
    print(f"要產生 {len(jobs)} 個音檔")
    done = 0
    for i in range(0, len(jobs), 60):
        batch = jobs[i:i + 60]
        res = await asyncio.gather(*[j[2] for j in batch])
        for (rel, h, _), ok in zip(batch, res):
            if ok:
                man[rel] = h
        done += len(batch)
        json.dump(man, open(MANIFEST, "w"), indent=0)
        print(f"  {done}/{len(jobs)}", flush=True)
    print(f"完成 {stats['ok']}，失敗 {len(stats['fail'])}")
    for f in stats["fail"][:20]:
        print("  失敗", f)


if __name__ == "__main__":
    only = set(sys.argv[1:]) or None
    asyncio.run(main(only))
