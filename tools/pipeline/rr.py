"""韓國官方羅馬拼音（文化體育觀光部 2000 年《국어의 로마자 표기법》，Revised Romanization）。

korean-romanizer 0.28.0 只照寫法逐字轉，官方拼法要反映的發音變化都沒做（實測：같이→gati、감사합니다→gamsahapnida、
신라→sinra；正確是 gachi、gamsahamnida、silla），所以自己轉：
- 子音取「實際唸法」（連音、鼻音化、流音化、顎化、送氣化都照唸法）；
- 但**緊音化不標**（학교 hakgyo、여권 yeogwon、삼겹살 samgyeopsal）：寫法是平音、唸法變緊音的，拼回平音；
- 母音取寫法（의 一律 ui，계 一律 gye，唸法的母音簡化不標）；
- 收尾音 ㄱ→k、ㄷ→t、ㅂ→p、ㄹ→l；ㄹ 在母音前是 r、ㄹㄹ 是 ll。
唸法和寫法的音節數對不上時（例如數字被唸成文字），直接用唸法。"""
import re

CHO = ["g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s", "ss", "", "j", "jj", "ch", "k", "t", "p", "h"]
JUNG = ["a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa", "wae", "oe", "yo", "u", "wo", "we", "wi", "yu", "eu", "ui", "i"]
# 收尾音代表音（唸法裡的收尾音已經是七個代表音之一，這裡保險起見全部對應）
JONG = ["", "k", "k", "k", "n", "n", "n", "t", "l", "k", "m", "l", "l", "l", "p", "l", "m", "p", "p", "t", "t", "ng", "t", "t", "k", "t", "p", "t"]
PLAIN_TENSE = {0: 1, 3: 4, 7: 8, 9: 10, 12: 13}  # ㄱ→ㄲ ㄷ→ㄸ ㅂ→ㅃ ㅅ→ㅆ ㅈ→ㅉ


def _parts(ch):
    c = ord(ch) - 0xAC00
    return c // 588, (c % 588) // 28, c % 28


def _is_syl(ch):
    return 0xAC00 <= ord(ch) <= 0xD7A3


def romanize(written, pron=None):
    """written：寫法；pron：實際唸法（同樣的空白與標點；沒有就等於寫法）"""
    pron = pron or written
    ws = [c for c in written if _is_syl(c)]
    ps = [c for c in pron if _is_syl(c)]
    aligned = len(ws) == len(ps)
    out, k, prev_final = [], 0, None
    for ch in pron:
        if not _is_syl(ch):
            out.append(ch)
            prev_final = None
            continue
        l, v, t = _parts(ch)
        if aligned:
            wl, wv, _ = _parts(ws[k])
            if PLAIN_TENSE.get(wl) == l:   # 緊音化不標
                l = wl
            v = wv                          # 母音照寫法
        k += 1
        ini = CHO[l]
        if l == 5 and prev_final == 8:      # ㄹㄹ → ll
            ini = "l"
        out.append(ini + JUNG[v] + JONG[t])
        prev_final = t
    s = "".join(out)
    return re.sub(r"\s+", " ", s).strip()


if __name__ == "__main__":
    tests = [("학교", "학꾜", "hakgyo"), ("같이", "가치", "gachi"), ("신라", "실라", "silla"), ("감사합니다", "감사함니다", "gamsahamnida"),
             ("여권", "여꿘", "yeogwon"), ("삼겹살", "삼겹쌀", "samgyeopsal"), ("목욕탕", "모굑탕", "mogyoktang"), ("희망", "히망", "huimang"),
             ("좋다", "조타", "jota"), ("결제", "결쩨", "gyeolje"), ("때밀이", "때미리", "ttaemiri"), ("필요하세요", "피료하세요", "piryohaseyo"),
             ("입국 심사는 어디에서 받아요?", "입꾹 씸사는 어디에서 바다요?", "ipguk simsaneun eodieseo badayo?"),
             ("카드로 결제하시겠어요?", "카드로 결제하시게써요?", "kadeuro gyeoljehasigesseoyo?"), ("맛있어요", "마시써요", "masisseoyo"),
             ("안녕하세요", None, "annyeonghaseyo"), ("종로", "종노", "jongno"), ("왕십리", "왕심니", "wangsimni"), ("별내", "별래", "byeollae")]
    bad = 0
    for w, p, want in tests:
        got = romanize(w, p)
        if got != want:
            bad += 1
        print(("OK " if got == want else "NG ") + w, got, "" if got == want else f"(want {want})")
    print("failures:", bad)
