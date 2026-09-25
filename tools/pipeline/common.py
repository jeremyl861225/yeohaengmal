"""韓文版管線共用：路徑、KRDict 索引、韓文字串工具。"""
import json, os, re, sys, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rr import romanize

WORK = os.environ.get("YH_WORK", os.path.expanduser("~/Desktop/Claude code/workspace/work/ko-travel-vocab"))
SOURCES = os.path.join(WORK, "sources")
BUILD = os.path.join(WORK, "build")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
G2P_PY = os.path.join(WORK, ".venv-g2p", "bin", "python")

HANGUL_RE = re.compile(r"[가-힣]")
HANJA_RE = re.compile(r"[㐀-鿿豈-﫿]")
LEVEL_SCORE = {"초급": 3, "중급": 2, "고급": 1}
SUFFIXES = {"하다", "되다", "히", "스럽다", "롭다", "적", "시키다", "당하다"}


def has_hangul(s):
    return bool(HANGUL_RE.search(s or ""))


def clean_pron(p):
    """KRDict 發音欄：拿掉長音記號 ː，多個唸法取第一個"""
    return (p or "").replace("ː", "").replace(":", "").strip()


def norm_key(s):
    """句子鍵：只留韓文、數字與英文字母（空白、標點、分寫差異都不算）"""
    return re.sub(r"[^가-힣0-9a-zA-Z]", "", s or "").lower()


def loose_roma(s):
    """羅馬拼音寬鬆鍵（和 App 的 romaKey 同一套）：g/k、d/t、b/p、j/ch、r/l 不分，eo→o、eu→u、ae→e，重複字母收成一個"""
    s = re.sub(r"[^a-z]", "", (s or "").lower())
    s = s.replace("eo", "o").replace("eu", "u").replace("ae", "e")
    s = s.replace("g", "k").replace("d", "t").replace("b", "p").replace("j", "ch").replace("r", "l")
    return re.sub(r"([a-z])\1+", r"\1", s)


@functools.lru_cache(maxsize=1)
def krdict():
    """回傳 (entries, by_w, by_id)"""
    with open(os.path.join(BUILD, "krdict.json"), encoding="utf-8") as f:
        entries = json.load(f)
    by_w, by_id = {}, {}
    # 관용구／속담 是巢在母詞條裡的子詞條，**和母詞條共用同一個 id**（물 與「물이 너무 맑으면…」都是 17596），不收
    entries = [e for e in entries if e["unit"] not in ("관용구", "속담")]
    for e in entries:
        e["pron1"] = clean_pron(e["pron"][0]) if e["pron"] else ""
        by_w.setdefault(e["w"], []).append(e)
        by_id[e["id"]] = e
    return entries, by_w, by_id


@functools.lru_cache(maxsize=1)
def roma_index():
    """KRDict 單字的官方拼音（依唸法）→ 詞條，給只有羅馬拼音的英文來源比對用"""
    entries, _, _ = krdict()
    idx = {}
    for e in entries:
        if e["unit"] != "단어" or " " in e["w"] or not has_hangul(e["w"]):
            continue
        k = loose_roma(romanize(e["w"], e["pron1"] or None))
        if k:
            idx.setdefault(k, []).append(e)
    return idx


def hanja_marks(word, origin):
    """KRDict 原語欄 → 逐段對齊的漢字標記。原語欄是漢字、韓文、外文混寫，有時用空白分段：
    「空港」「安寧 하다」「豫約하다」「三 겹살」「찜질 房」「空港bus」。依文字種類切成段：
    漢字段一字對一個音節；韓文段要和寫法逐字相同；外文段（bus）只能在最後（對應剩下的外來語音節，不標）。
    對不上就回傳 None。回傳 [(起, 迄, 漢字)]，位置是 word 的音節位置。"""
    if not origin or not HANJA_RE.search(origin):
        return None
    origin = origin.replace("▽", "")
    if "[" in origin or "←" in origin:
        return None      # 外來語的語源註記（←ton[豚]kasu）不標
    origin = re.sub(r"([\u3400-\u9fff\uf900-\ufaff]+)(?:/[\u3400-\u9fff\uf900-\ufaff]+)+", r"\1", origin)  # 異體寫法 感歎/感嘆 取第一個
    runs = re.findall(r"[\u3400-\u9fff\uf900-\ufaff]+|[가-힣]+|[A-Za-z][A-Za-z\-' ]*", origin)
    syl = list(word)
    pos, marks = 0, []
    for i, seg in enumerate(runs):
        if HANJA_RE.match(seg):
            n = len(seg)
            if pos + n > len(syl) or not all(has_hangul(c) for c in syl[pos:pos + n]):
                return None
            marks.append((pos, pos + n, seg))
            pos += n
        elif has_hangul(seg):
            if "".join(syl[pos:pos + len(seg)]) != seg:
                return None
            pos += len(seg)
        else:
            # 外文段（gas 管 → 가스관、空港bus → 공항버스）：長度＝剩下的音節扣掉後面各段需要的音節
            need = sum(len(r) for r in runs[i + 1:] if HANJA_RE.match(r) or has_hangul(r))
            if any(not (HANJA_RE.match(r) or has_hangul(r)) for r in runs[i + 1:]):
                return None
            n = len(syl) - pos - need
            if n < 1:
                return None
            pos += n
    if marks and pos < len(syl) and "".join(syl[pos:]) in SUFFIXES:
        pos = len(syl)   # 原語欄漏寫了後綴（開化 → 개화하다）
    return marks if marks and pos == len(syl) else None


def apply_marks(text, marks):
    """把 [(起, 迄, 漢字)] 套到字串上：{공항|空港}버스"""
    syl = list(text)
    out, last = [], 0
    for a, b, h in marks:
        out.append("".join(syl[last:a]))
        out.append("{" + "".join(syl[a:b]) + "|" + h + "}")
        last = b
    out.append("".join(syl[last:]))
    return "".join(out)
