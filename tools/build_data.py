"""組出 App 用的 data/cards.json，並做資料檢查。韓文版。

輸入：workspace/build/selection.json（排名、分級、單元）、build/author/out-*.json（中文、例句）、
      build/author/fix.json（人工修正，可無，格式同撰寫輸出、只寫要改的欄位）、build/sources_meta.json、build/unit_names.json
輸出：data/cards.json、build/tts.json（朗讀文字，給 make_audio.py）、build/qa.json（檢查報告）

每張卡：
- w：韓文＋漢字標記 {공항|空港}（漢字取 KRDict 原語欄逐段對齊；句子裡只標字典裡沒有歧義的詞）
- r：實際唸法。字典查得到的詞用 KRDict 發音欄；其他（活用形、固定說法、多個詞、外來語）用 g2pk2，
     再用字典把 g2pk 抓不到的詞彙性緊音化補回去（여권 번호 → 여꿘 번호）。句子卡的 r 就是寫法本身（不顯示）。
- rm：官方羅馬拼音（pipeline/rr.py：子音照唸法、母音照寫法、不標緊音化）
"""
import json, os, re, sys, glob, datetime, collections, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from rr import romanize
from themes import theme_list, family_list
from kiwipiepy import Kiwi
import opencc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIERS = [{"id": 1, "name": "必備"}, {"id": 2, "name": "常用"}, {"id": 3, "name": "進階"}]
VOICE_NAMES = ("SunHi", "InJoon")      # 和 make_audio.py 的 VOICES 一致；換聲音時兩邊一起改
CREDITS = (f"發音：Microsoft 神經語音 {VOICE_NAMES[0]}（女聲）與 {VOICE_NAMES[1]}（男聲），以 edge-tts 產生，僅供個人學習。"
           "漢字與實際唸法校對：國立國語院《韓國語基礎辭典》（CC BY-SA 2.0 KR）；羅馬拼音依韓國文化體育觀光部《國語的羅馬字表記法》轉換。"
           "字卡以外的字：離線字典取自同一部辭典的常用詞，發音用手機內建語音。韓文字型：Noto Serif KR（SIL Open Font License 1.1）。"
           "例句與中文解釋由 AI 撰寫，經字典與規則檢查。")
s2tw = opencc.OpenCC("s2tw")
# 台灣常用、OpenCC s2tw 卻會改掉的字，不算簡體：台→臺、只→隻、注→註、蔘雞湯→參雞湯、里脊→裡脊、了解→瞭解
#（撰寫代理曾為了過檢查把「蔘雞湯」改成「參雞湯」，所以白名單要和撰寫規格一致）
TW_OK = set("台只注蔘里了")
kiwi = Kiwi()
entries, by_w, by_id = krdict()
CONTENT = {"NNG", "NNP", "NP", "NR", "VV", "VA", "VX", "MAG", "XR"}
NATIVE_NUM = r"(?:한|두|세|네|다섯|여섯|일곱|여덟|아홉|열|스무|스물)"
SINO_NUM = r"(?:일|이|삼|사|오|육|칠|팔|구|십|백|천|만)"
NATIVE_COUNTERS = r"(?:개|명|시|살|잔|병|마리|시간|장|권|벌|번째)"
SINO_COUNTERS = r"(?:층|분|원|인분|호선|월|일|년)"


def odd_chars(s):
    """中文欄位裡的簡體字；「」『』裡引用的原文不算"""
    s = re.sub(r"「[^」]*」|『[^』]*』", "", s)
    return "".join(sorted({a for a, b in zip(s, s2tw.convert(s)) if a != b and a not in TW_OK}))


# ---------- 唸法 ----------
G2P_CACHE = os.path.join(BUILD, "g2p_cache.json")
_g2p = json.load(open(G2P_CACHE, encoding="utf-8")) if os.path.exists(G2P_CACHE) else {}


def g2p_many(texts):
    todo = [t for t in dict.fromkeys(texts) if t and t not in _g2p]
    if todo:
        res = subprocess.run([G2P_PY, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline", "g2p_batch.py")],
                             input=json.dumps(todo, ensure_ascii=False), capture_output=True, text=True, check=True)
        for t, p in zip(todo, json.loads(res.stdout)):
            _g2p[t] = p
        json.dump(_g2p, open(G2P_CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    return {t: _g2p.get(t, t) for t in texts}


TENSE = {0: 1, 3: 4, 7: 8, 9: 10, 12: 13}


def _parts(ch):
    c = ord(ch) - 0xAC00
    return c // 588, (c % 588) // 28, c % 28


def upgrade_tense(pron, ref):
    """ref（字典唸法）裡是緊音、pron 同位置是平音的，改成緊音；其餘照 pron（不把 g2pk 的連讀變化改回去）"""
    if len(pron) != len(ref):
        return pron
    out = []
    for a, b in zip(pron, ref):
        if "가" <= a <= "힣" and "가" <= b <= "힣":
            la, va, ta = _parts(a)
            lb, _, _ = _parts(b)
            if TENSE.get(la) == lb:
                a = chr(0xAC00 + (lb * 21 + va) * 28 + ta)
        out.append(a)
    return "".join(out)


def entry_for(word):
    """一個語節（去掉標點）→ 字典詞條：先查寫法，再用 kiwipiepy 還原原形；回傳 (詞條清單, 對到的形)"""
    if word in by_w:
        return by_w[word], word
    toks = kiwi.tokenize(word)
    core = [t for t in toks if t.tag.split("-")[0] in CONTENT or t.tag.startswith("XS")]
    lem = None
    if len(core) == 1:
        t = core[0]
        lem = t.form + "다" if t.tag.split("-")[0] in ("VV", "VA", "VX") else t.form
    elif len(core) == 2 and core[0].tag.split("-")[0] in ("NNG", "NNP", "XR") and core[1].tag.startswith("XS"):
        lem = core[0].form + core[1].form + "다"
    if lem and lem in by_w:
        return by_w[lem], lem
    return [], None


def pron_of(head, lemma, lemma_pron):
    """單字卡的實際唸法"""
    text = head.replace("~", "").strip()
    if text == lemma and lemma_pron:
        return lemma_pron
    base = g2p_many([text])[text]
    words = text.split(" ")
    pw = base.split(" ")
    if len(words) == len(pw):
        fixed = []
        for w, p in zip(words, pw):
            ref = None
            core = re.sub(r"[^가-힣]", "", w)
            if core == lemma and lemma_pron:
                ref = lemma_pron
            elif core in by_w:
                prons = {e["pron1"] for e in by_w[core] if e["pron1"]}
                ref = prons.pop() if len(prons) == 1 else None
            elif len(core) >= 3 and len(p) == len(core):
                # 複合詞（여권사진）：找語節開頭最長的字典詞，用它的唸法補緊音，其餘照 g2pk
                for n in range(len(core) - 1, 1, -1):
                    prons = {e["pron1"] for e in by_w.get(core[:n], []) if e["pron1"]}
                    if len(prons) == 1:
                        head_pron = prons.pop()
                        if len(head_pron) == n:
                            ref = head_pron + p[n:]
                        break
            elif lemma and lemma_pron and lemma.endswith("다") and core.startswith(lemma[:-1]) and len(lemma) > 2:
                stem = lemma[:-1]
                # 活用形：只在詞幹後面接的是子音開頭（不連音）時，才用字典唸法補緊音
                nxt = core[len(stem):len(stem) + 1]
                if nxt and _parts(nxt)[0] != 11:
                    ref = lemma_pron[:len(stem)] + p[len(stem):] if len(p) >= len(stem) else None
            fixed.append(upgrade_tense(p, ref) if ref and re.sub(r"[^가-힣]", "", p) == p else p)
        base = " ".join(fixed)
    return base


# ---------- 漢字標記 ----------
def pick_origin(cands):
    """同一個寫法有好幾個詞條時，挑漢字：只有一種漢字、或某個漢字詞的難度明顯最基本（역：驛 초급 vs 役 고급）才挑；
    有同樣常用的非漢字同形詞（말：話 vs 末）或兩個一樣常用的漢字詞（차：茶／車）就不標"""
    by_origin, native_best = {}, 0
    for e in cands:
        sc = LEVEL_SCORE.get(e["level"], 0)
        o = e["origin"]
        if o and HANJA_RE.search(o) and not re.search(r"[A-Za-z←\[]", o):
            by_origin[o] = max(by_origin.get(o, 0), sc)
        else:
            native_best = max(native_best, sc)
    if not by_origin:
        return None
    ranked = sorted(by_origin.items(), key=lambda kv: -kv[1])
    top_o, top_s = ranked[0]
    if native_best >= 2 and top_s <= native_best:
        return None
    if len(ranked) == 1 or (top_s >= 2 and top_s > ranked[1][1]):
        return top_o
    return None


def eojeol_marks(word, prefer=None, direct=False):
    """一個語節的漢字標記（位置是語節內的字元位置）。prefer：這張卡本身的詞條（原形, 原語），先試它，對不上再查字典"""
    m = re.match(r"^([^가-힣]*)([가-힣]+)", word)
    if not m:
        return []
    lead, core = len(m.group(1)), m.group(2)
    tries = []
    if direct and prefer and prefer[1]:
        tries.append((core, prefer[1]))        # 單一個詞的卡：選字時直接給的原語，先和卡片自己的寫法對齊（밀면＝밀＋麵）
    if prefer and prefer[0] and prefer[1]:
        tries.append(prefer)
    cands, lem = entry_for(core)
    if cands:
        o = pick_origin(cands)
        if o:
            tries.append((lem, o))
    for lemma, origin in tries:
        marks = hanja_marks(lemma, origin)
        if not marks:
            continue
        common = 0
        while common < min(len(lemma), len(core)) and lemma[common] == core[common]:
            common += 1
        kept = [(a + lead, b + lead, h) for a, b, h in marks if b <= common]
        if kept:
            return kept
    return []


def markup(head, kind, lemma, origin, native=False):
    """native：這張卡本身已知不是漢字詞（選字時把原語清成空白，或字典對到的詞沒有漢字）——
    卡片自己那個詞不要再拿字典的同形異義字來標（안심「里肌」不能標成 安心）"""
    words = head.split(" ")
    out = []
    stem = lemma[:-1] if lemma.endswith("다") and len(lemma) > 1 else lemma
    segs = origin.split() if origin else []
    per_word = kind == "w" and len(words) > 1 and len(segs) == len(words)   # 즉시 환급 ↔ 卽時 還給：逐詞對齊
    for i, w in enumerate(words):
        core = re.sub(r"[^가-힣]", "", w)
        if kind == "w" and native and (len(words) == 1 or (stem and core.startswith(stem))):
            out.append(w)
            continue
        if per_word and HANJA_RE.search(segs[i]):
            mk = hanja_marks(core, segs[i])
            if mk:
                lead = len(re.match(r"^[^가-힣]*", w).group(0))
                out.append(apply_marks(w, [(a + lead, b + lead, h) for a, b, h in mk]))
                continue
        prefer = (lemma, origin) if kind == "w" else None
        mk = eojeol_marks(w, prefer, direct=len(words) == 1)
        out.append(apply_marks(w, mk) if mk else w)
    return " ".join(out)


# ---------- 檢查 ----------
def head_in_example(head, ex, lemma):
    h = norm_key(head.replace("~", ""))
    e = norm_key(ex)
    if h and h in e:
        return True
    lemmas = set()
    toks = kiwi.tokenize(ex)
    for i, t in enumerate(toks):
        tag = t.tag.split("-")[0]
        if tag in ("VV", "VA", "VX"):
            lemmas.add(t.form + "다")
        elif tag in ("NNG", "NNP", "NR", "NP", "MAG", "XR"):
            lemmas.add(t.form)
            if i + 1 < len(toks) and toks[i + 1].tag.startswith("XS"):
                lemmas.add(t.form + toks[i + 1].form + "다")
    for i in range(len(toks) - 1):
        a, b = toks[i], toks[i + 1]
        if b.form == "하" and b.tag.split("-")[0] in ("VV", "XSV", "XSA"):
            lemmas.add(a.form + "하다")                                  # 잘해요 → 잘하다、못해요 → 못하다
        if a.tag.split("-")[0] == "VV" and i + 2 < len(toks) and b.tag == "EC" and toks[i + 2].tag.split("-")[0] in ("VX", "VV"):
            c = toks[i + 2]
            lemmas.add(a.form + b.form + c.form + "다")
            lemmas.add(ex[a.start:c.start + c.len] + "다")                # 用原文的字（물어볼게요 → 물어보다；kiwi 會把詞幹還原成 묻）
    if lemma and lemma in lemmas:
        return True
    hl = entry_for(re.sub(r"[^가-힣]", "", head))[1]
    if hl and hl in lemmas:
        return True
    # 詞幹（예약하다 → 예약했어요）
    stem = re.sub(r"(하다|다)$", "", h)
    if len(stem) >= 2 and stem in e:
        return True
    if h.endswith("다") and len(h) >= 2:
        st = h[:-1]
        last = st[-1]
        l, v, t = _parts(last)
        body = st[:-1]
        # 單音節詞幹接語尾（들다 → 들어、타다 → 타요）
        if re.search(re.escape(st) + r"(어|아|여|었|았|을|을게|는|고|지|세|시|면|니|ㄹ)", e) or (len(st) == 1 and re.search(re.escape(st) + r"[가-힣]", e)):
            return True
        # ㄹ 脫落（알다 → 아세요、만들다 → 만드세요）
        if t == 8 and re.search(re.escape(body + chr(0xAC00 + (l * 21 + v) * 28)) + r"(세|시|는|니|네|십|ㅂ)", e):
            return True
        # ㅂ 不規則（돕다 → 도와요、춥다 → 추워요、맵다 → 매워요）
        if t == 17 and re.search(re.escape(body + chr(0xAC00 + (l * 21 + v) * 28)) + r"(와|워|우)", e):
            return True
        # ㄷ 不規則（걷다 → 걸어요、듣다 → 들어요）、르 不規則（모르다 → 몰라요）、ㅅ 不規則（낫다 → 나아요）
        if t == 7 and re.search(re.escape(body + chr(0xAC00 + (l * 21 + v) * 28 + 8)) + r"(어|으|었)", e):
            return True
        if last == "르" and body and re.search(re.escape(body[:-1] + chr(ord(body[-1]) + 8) if body else "") + r"(라|러)", e):
            return True
        if t == 19 and re.search(re.escape(body + chr(0xAC00 + (l * 21 + v) * 28)) + r"(아|어|으)", e):
            return True
    return False


POLITE_END = re.compile(r"(요|니다|니까|세요|시오|죠|네요|군요|래요|대요|까요|게요|아요|어요|해요|예요|에요)$")


def polite(ex):
    t = re.sub(r"[.?!。！？…~\s]+$", "", ex)
    if POLITE_END.search(t):
        return True
    last = t.split(" ")[-1] if t else ""
    return last in ("네", "예", "아니요", "아뇨", "감사합니다", "고맙습니다", "안녕하세요")


def counter_problems(text):
    bad = []
    bad += re.findall(rf"\b{SINO_NUM}\s?{NATIVE_COUNTERS}(?![가-힣])", text)
    bad += re.findall(rf"(?<![가-힣]){NATIVE_NUM}\s?{SINO_COUNTERS}(?![가-힣])", text)
    bad += re.findall(rf"[0-9]+\s?{NATIVE_COUNTERS}(?![가-힣])", text)     # 固有語量詞前寫阿拉伯數字：語音會唸成漢字語數字
    return bad


def main():
    sel = json.load(open(os.path.join(BUILD, "selection.json"), encoding="utf-8"))
    authored = {}
    for f in sorted(glob.glob(os.path.join(BUILD, "author", "out-*.json"))):
        for d in json.load(open(f, encoding="utf-8")):
            authored[d["id"]] = d
    fixp = os.path.join(BUILD, "author", "fix.json")
    if os.path.exists(fixp):
        for d in json.load(open(fixp, encoding="utf-8")):
            authored.setdefault(d["id"], {}).update(d)
    themes = theme_list()
    tname = {t["id"]: t["name"] for t in themes}

    qa = collections.defaultdict(list)
    cards, tts, dropped = [], {}, set()
    rows = []
    for c in sel["cards"]:
        a = authored.get(c["id"], {})
        if a.get("drop"):
            qa["dropped"].append([c["id"], c["head"], a.get("why", ""), c.get("keys", [])])
            dropped.add(c["id"])
            continue
        head = re.sub(r"\s+", " ", (a.get("head") or c["head"]).strip())
        kind = c["kind"]
        if a.get("pos"):
            kind = "p" if a["pos"] == "句子" else "w"
        origin = a["origin"] if "origin" in a else c.get("origin", "")
        rows.append((c, a, head, kind, origin))
    # 一次跑完 g2p（句子與不在字典裡的詞）
    g2p_many([h.replace("~", "").strip() for _, _, h, _, _ in rows] + [re.sub(r"[^가-힣0-9 ]", "", h).strip() for _, _, h, _, _ in rows])

    for c, a, head, kind, origin in rows:
        lemma, lemma_pron = c.get("lemma", ""), c.get("lemma_pron", "")
        if a.get("head") and a["head"] != c["head"] and norm_key(a["head"]) != norm_key(lemma):
            lemma_pron = lemma_pron if head.startswith(lemma.rstrip("다")) else ""
        native = kind == "w" and not (origin and HANJA_RE.search(origin)) and (c.get("origin_set") or bool(lemma))
        w = markup(head, kind, lemma, origin, native)
        plain_head = re.sub(r"\{([^|{}]+)\|[^{}]+\}", r"\1", w)
        if kind == "w":
            r = pron_of(head, lemma, lemma_pron)
            spoken = re.sub(r"[^가-힣0-9 ]", "", head).strip()
            noun = a.get("pos", "") in ("名詞", "依存名詞", "代名詞", "數詞", "量詞")
            rm = romanize(re.sub(r"[^가-힣 ]", "", head).strip(), re.sub(r"[^가-힣 ]", "", r).strip(), noun=noun) if re.search(r"[가-힣]", head) else head
        else:
            r = plain_head
            spoken = re.sub(r"[^가-힣0-9 .,?!]", "", head.replace("~", "")).strip()
            p = _g2p.get(re.sub(r"[^가-힣0-9 ]", "", head).strip(), "")
            rm = romanize(re.sub(r"[^가-힣 ?.!,]", "", head).strip(), re.sub(r"[^가-힣 ?.!,]", "", p).strip() if p else None)
        ex = a.get("ex", "").strip()
        zh = a.get("zh", "").strip()
        card = {"id": c["id"], "w": w, "r": r, "rm": rm, "zh": zh, "pos": a.get("pos", ""),
                "th": c["theme"], "t": c["tier"], "rank": c["rank"], "n": c["n"], "no": c["no"],
                "ex": ex, "exz": a.get("exz", "").strip(), "note": a.get("note", "").strip(), "k": kind}
        if not card["note"]:
            del card["note"]
        cards.append(card)
        tts[c["id"]] = {"w": spoken or plain_head, "x": ex}

        # ---- 檢查 ----
        if re.search(r"_{2,}|…|\.\.\.|~|\(|\)", head):
            qa["pattern_head"].append([c["id"], head])      # 空格、刪節號、括號：語音念不好，改成具體的一句或拿掉括號
        if kind == "w" and origin and HANJA_RE.search(origin) and "{" not in w and not re.search(r"[A-Za-z]", origin):
            qa["hanja_unaligned"].append([c["id"], head, origin])
        if not zh:
            qa["missing_zh"].append(c["id"])
        if not ex:
            qa["missing_ex"].append([c["id"], head])
            continue
        odd = odd_chars(zh + card["exz"] + card.get("note", ""))
        if odd:
            qa["simplified_chinese"].append([c["id"], odd, zh, card["exz"], card.get("note", "")])
        if re.search(r"[{}|]", ex) or HANJA_RE.search(ex):
            qa["ex_markup"].append([c["id"], ex])
        if kind != "p" and not head_in_example(head, ex, lemma):
            qa["head_not_in_example"].append([c["id"], head, ex])
        if not polite(ex):
            qa["register"].append([c["id"], ex])
        cp = counter_problems(ex) + (counter_problems(head) if kind == "w" else [])
        if cp:
            qa["counter"].append([c["id"], head, ex, cp])
        if len(ex) > 40:
            qa["long_example"].append([c["id"], ex])

    # 課名：build/unit_names.json（每課的子題名稱，全 App 不重複）；沒有的話退回「主題＋編號」
    np_ = os.path.join(BUILD, "unit_names.json")
    names = json.load(open(np_, encoding="utf-8")) if os.path.exists(np_) else {}
    units = []
    for u in sel["units"]:
        ids = [x for x in u["cards"] if x not in dropped]
        if not ids:
            continue
        title = names.get(u["id"]) or tname[u["th"]] + (f" {u['part']}" if u["parts"] > 1 else "")
        units.append({**u, "cards": ids, "title": title})
    missing = [u["id"] for u in units if u["id"] not in names]
    if names and missing:
        qa["unit_name_missing"] = missing
    dup = [t for t, n in collections.Counter(u["title"] for u in units).items() if n > 1]
    if dup:
        qa["unit_title_duplicate"] = dup

    srcs = json.load(open(os.path.join(BUILD, "sources_meta.json"), encoding="utf-8"))
    audio_bytes = collections.Counter()
    for card in cards:
        for v in ("f", "m"):
            for suf in ("", "x"):
                p = os.path.join(ROOT, "audio", v, f"{card['id']}{suf}.mp3")
                if os.path.exists(p):
                    audio_bytes[str(card["t"])] += os.path.getsize(p)
    data = {
        "meta": {"version": datetime.date.today().isoformat(), "count": len(cards),
                 "sources": [{"id": s["id"], "title": s["title"], "url": s["url"], "lang": s["lang"]} for s in srcs],
                 "audioBytes": dict(audio_bytes), "credits": CREDITS},
        "tiers": TIERS, "themes": themes, "families": family_list(), "units": units, "cards": cards,
    }
    out_path = os.environ.get("YH_DATA_OUT", os.path.join(ROOT, "data", "cards.json"))   # 試跑時可以寫到別處，不動線上的 cards.json
    json.dump(data, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    json.dump(tts, open(os.path.join(BUILD, "tts.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    json.dump(qa, open(os.path.join(BUILD, "qa.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    size = os.path.getsize(out_path)
    print(f"{len(cards)} 張卡、{len(units)} 課 → {out_path}（{size / 1024:.0f} KB）")
    for k, v in qa.items():
        print(f"  檢查 {k}: {len(v)}")


if __name__ == "__main__":
    main()
