"""四十音課程的資料（2026-10-02 使用者要求「韓文增加四十音課程，由你發揮」；日文版旅ことば同時加了五十音，共用 js/letters.js）。

四十音＝韓文字母 40 個：基本母音 10、複合母音 11、基本子音 14、硬音（雙子音）5。課程 9 課：
母音兩課 → 子音兩課 → 硬音 → 平音・激音・硬音對照（聽力最難的地方）→ 複合母音兩課 → 收音（받침）七個代表音。

輸出：
- data/letters.json：課程＋四十音表（js/letters.js 讀）
- build/letters_tts.json（工作區）：要合成的音檔清單，給 tools/make_extra_audio.py

每個字母：字母、羅馬拼音（官方拼法）、名稱（子音：기역、니은…）、代表音節（母音配 ㅇ、子音配 ㅏ；音檔念的就是它，放慢 30%）、
注音近似的提示（台灣人好記；只是近似，標明「像」）、例字（字卡裡第一個音節合條件、旅遊頻率最高的字；播字卡原本的音檔）。"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get("YH_WORK", os.path.expanduser("~/Desktop/Claude code/workspace/work/ko-travel-vocab"))
RUBY = re.compile(r"\{([^|{}]+)\|[^{}]+\}")
CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
JONG = ["", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
# 收音的七個代表音
REP = {"ㄱ": "ㄱ", "ㄲ": "ㄱ", "ㅋ": "ㄱ", "ㄳ": "ㄱ", "ㄺ": "ㄱ", "ㄴ": "ㄴ", "ㄵ": "ㄴ", "ㄶ": "ㄴ", "ㄷ": "ㄷ", "ㅅ": "ㄷ", "ㅆ": "ㄷ", "ㅈ": "ㄷ", "ㅊ": "ㄷ",
       "ㅌ": "ㄷ", "ㅎ": "ㄷ", "ㄹ": "ㄹ", "ㄼ": "ㄹ", "ㄽ": "ㄹ", "ㄾ": "ㄹ", "ㅀ": "ㄹ", "ㅁ": "ㅁ", "ㄻ": "ㅁ", "ㅂ": "ㅂ", "ㅍ": "ㅂ", "ㅄ": "ㅂ", "ㄿ": "ㅂ", "ㅇ": "ㅇ"}


def split(s):
    c = ord(s) - 0xAC00
    if not 0 <= c < 11172:
        return None
    return CHO[c // 588], JUNG[c % 588 // 28], JONG[c % 28]


def compose(cho, jung, jong=""):
    return chr(0xAC00 + CHO.index(cho) * 588 + JUNG.index(jung) * 28 + JONG.index(jong))


VOWELS = {  # 字母: (羅馬拼音, 注音近似)
    "ㅏ": ("a", "像注音 ㄚ"), "ㅓ": ("eo", "介於 ㄛ 和 ㄜ 之間：嘴巴張開、不嘟嘴"), "ㅗ": ("o", "像 ㄛ，但嘴唇圓、往前嘟"),
    "ㅜ": ("u", "像 ㄨ"), "ㅡ": ("eu", "嘴角往兩邊拉、扁扁的 ㄜ"), "ㅣ": ("i", "像 ㄧ"),
    "ㅑ": ("ya", "ㄧ＋ㅏ，像「呀」"), "ㅕ": ("yeo", "ㄧ＋ㅓ"), "ㅛ": ("yo", "ㄧ＋ㅗ，像「喲」"), "ㅠ": ("yu", "ㄧ＋ㅜ，像英文 you"),
    "ㅐ": ("ae", "像 ㄝ（嘴巴張大一點）"), "ㅔ": ("e", "像 ㄝ；現在和 ㅐ 幾乎同音"), "ㅒ": ("yae", "ㄧ＋ㅐ，像「耶」"), "ㅖ": ("ye", "ㄧ＋ㅔ，像「耶」"),
    "ㅘ": ("wa", "ㅗ＋ㅏ，像「哇」"), "ㅙ": ("wae", "ㅗ＋ㅐ，像「ㄨㄝ」"), "ㅚ": ("oe", "現在多念「ㄨㄝ」，和 ㅙ、ㅞ 很像"),
    "ㅝ": ("wo", "ㅜ＋ㅓ，像「ㄨㄛ」"), "ㅞ": ("we", "ㅜ＋ㅔ，像「ㄨㄝ」"), "ㅟ": ("wi", "ㅜ＋ㅣ，像「威」快念"),
    "ㅢ": ("ui", "ㅡ＋ㅣ；在字中常念 ㅣ，當「的」念 ㅔ"),
}
CONS = {  # 字母: (羅馬拼音, 名稱, 注音近似)
    "ㄱ": ("g/k", "기역", "像 ㄍ；在字首比較像輕的 ㄎ"), "ㄴ": ("n", "니은", "像 ㄋ"), "ㄷ": ("d/t", "디귿", "像 ㄉ；在字首比較像輕的 ㄊ"),
    "ㄹ": ("r/l", "리을", "舌尖輕彈一下，介於 ㄌ 和 ㄖ 之間"), "ㅁ": ("m", "미음", "像 ㄇ"), "ㅂ": ("b/p", "비읍", "像 ㄅ；在字首比較像輕的 ㄆ"),
    "ㅅ": ("s", "시옷", "像 ㄙ；遇到 ㅣ 時像 ㄒ（시）"), "ㅇ": ("–/ng", "이응", "在字首不發音（아＝a）；當收音念 ng（ㄥ）"),
    "ㅈ": ("j", "지읒", "像 ㄗ 或 ㄐ，不送氣"), "ㅊ": ("ch", "치읓", "像 ㄘ 或 ㄑ，送氣"), "ㅋ": ("k", "키읔", "像 ㄎ，用力送氣"),
    "ㅌ": ("t", "티읕", "像 ㄊ，用力送氣"), "ㅍ": ("p", "피읖", "像 ㄆ，用力送氣"), "ㅎ": ("h", "히읗", "像 ㄏ"),
    "ㄲ": ("kk", "쌍기역", "喉嚨用力、不送氣的 ㄍ"), "ㄸ": ("tt", "쌍디귿", "喉嚨用力、不送氣的 ㄉ"), "ㅃ": ("pp", "쌍비읍", "喉嚨用力、不送氣的 ㄅ"),
    "ㅆ": ("ss", "쌍시옷", "用力、較尖的 ㄙ"), "ㅉ": ("jj", "쌍지읒", "喉嚨用力、不送氣的 ㄗ"),
}
FINALS = {  # 收音代表音: (例音節, 羅馬拼音, 說明)
    "ㄱ": ("각", "-k", "舌根頂住不放，不爆出聲（ㄲ、ㅋ 收尾也這樣念）"), "ㄴ": ("간", "-n", "像 ㄢ 的 n"),
    "ㄷ": ("갇", "-t", "舌尖頂住上排牙齦不放（ㅅ ㅆ ㅈ ㅊ ㅌ ㅎ 收尾都這樣念）"), "ㄹ": ("갈", "-l", "舌尖輕輕頂住上顎，不捲舌"),
    "ㅁ": ("감", "-m", "雙唇閉起來（像台語「甘」的尾音）"), "ㅂ": ("갑", "-p", "雙唇閉住不放（ㅍ 收尾也這樣念）"), "ㅇ": ("강", "-ng", "像 ㄤ 的 ng"),
}
ROMA_CHO = {"ㄱ": "g", "ㄲ": "kk", "ㄷ": "d", "ㄸ": "tt", "ㅂ": "b", "ㅃ": "pp", "ㅅ": "s", "ㅆ": "ss", "ㅈ": "j", "ㅉ": "jj", "ㅊ": "ch", "ㅋ": "k", "ㅌ": "t", "ㅍ": "p"}

TTS = []


def add_tts(key, text, rate="-30%"):
    TTS.append({"file": f"audio/{key}.mp3", "text": text, "voice": "f", "rate": rate})
    return key


class Examples:
    def __init__(self, cards):
        self.cards = sorted((c for c in cards if c.get("k") == "w"), key=lambda c: (c.get("rank") or 99999, c.get("sq") or 99999))
        self.used = set()

    def pick(self, test):
        for c in self.cards:
            w = RUBY.sub(r"\1", c["w"]).replace(" ", "")
            if not w or c["id"] in self.used or not (1 <= len(w) <= 4):
                continue
            p = split(w[0])
            if p and test(*p):
                self.used.add(c["id"])
                return c["id"]
        return None


def vowel(ch, ex):
    roma, hint = VOWELS[ch]
    syl = compose("ㅇ", ch)
    d = {"ch": ch, "roma": roma, "syl": syl, "hint": hint, "a": add_tts(f"l/v-{roma}", syl)}
    e = ex.pick(lambda c, j, f: c == "ㅇ" and j == ch)
    if e:
        d["ex"] = e
    return d


def cons(ch, ex):
    roma, name, hint = CONS[ch]
    syl = compose(ch, "ㅏ")
    key = "l/c-" + ("ieung" if ch == "ㅇ" else roma.replace("/", ""))
    d = {"ch": ch, "roma": roma, "name": name, "syl": syl, "hint": hint, "a": add_tts(key, syl)}
    e = ex.pick(lambda c, j, f: c == ch)
    if e:
        d["ex"] = e
    return d


def final(ch, ex):
    syl, roma, hint = FINALS[ch]
    d = {"ch": syl, "roma": "ga" + roma.lstrip("-") if ch != "ㅇ" else "gang", "name": f"收音 {ch}", "hint": hint,
         "a": add_tts(f"l/f-{roma.lstrip('-')}", syl)}
    d["roma"] = {"ㄱ": "gak", "ㄴ": "gan", "ㄷ": "gat", "ㄹ": "gal", "ㅁ": "gam", "ㅂ": "gap", "ㅇ": "gang"}[ch]
    e = ex.pick(lambda c, j, f: f and REP.get(f) == ch)
    if e:
        d["ex"] = e
    return d


def triple(cho_list):
    """平音・激音・硬音對照：同一個母音 ㅏ"""
    row = []
    kinds = {0: "平音", 1: "激音", 2: "硬音"}
    for i, c in enumerate(cho_list):
        syl = compose(c, "ㅏ")
        roma = ROMA_CHO[c] + "a"
        kind = "平音" if c in "ㄱㄷㅂㅈㅅ" else "激音" if c in "ㅋㅌㅍㅊ" else "硬音"
        row.append({"ch": syl, "roma": roma, "zh": kind, "a": add_tts(f"l/p-{roma}", syl)})
    return row


def main():
    cards = json.load(open(os.path.join(ROOT, "data", "cards.json"), encoding="utf-8"))["cards"]
    ex = Examples(cards)
    V = lambda s: [vowel(c, ex) for c in s]
    K = lambda s: [cons(c, ex) for c in s]
    lessons1 = [
        {"id": "v1", "title": "基本母音（一）", "sub": "ㅏ ㅓ ㅗ ㅜ ㅡ ㅣ", "rows": [V("ㅏㅓㅗ"), V("ㅜㅡㅣ")],
         "notes": ["韓文是拼音文字：子音＋母音（＋收音）組成一個方塊字，例如 ㄱ＋ㅏ＝가。",
                   "母音單獨寫時前面要加不發音的 ㅇ：아、어、오…（音檔念的就是這個）。",
                   "直的母音（ㅏ ㅓ ㅣ）子音放左邊；橫的母音（ㅗ ㅜ ㅡ）子音放上面：가、고。",
                   "ㅓ 和 ㅗ 最難分：ㅓ 嘴巴張開不嘟嘴，ㅗ 嘴唇圓圓往前嘟。"]},
        {"id": "v2", "title": "基本母音（二）", "sub": "ㅑ ㅕ ㅛ ㅠ", "rows": [V("ㅑㅕ"), V("ㅛㅠ")],
         "notes": ["多一短橫＝前面加一個「ㄧ」：ㅏ→ㅑ、ㅓ→ㅕ、ㅗ→ㅛ、ㅜ→ㅠ。", "到這裡，十個基本母音就學完了：ㅏ ㅑ ㅓ ㅕ ㅗ ㅛ ㅜ ㅠ ㅡ ㅣ（字典也照這個順序排）。"]},
        {"id": "c1", "title": "基本子音（一）", "sub": "ㄱ ㄴ ㄷ ㄹ ㅁ ㅂ ㅅ", "rows": [K("ㄱㄴㄷㄹ"), K("ㅁㅂㅅ")],
         "notes": ["音檔念的是子音配 ㅏ：가、나、다…；下面的小字是字母的名稱（기역、니은…）。",
                   "ㄱ ㄷ ㅂ 在字首聽起來像輕的 ㄎ ㄊ ㄆ，夾在母音中間就變成 ㄍ ㄉ ㄅ：고기（ko-gi，肉）。",
                   "ㄹ 在字首、母音之間是輕彈的 r，收尾是 l：라면（拉麵）、서울（首爾）。"]},
        {"id": "c2", "title": "基本子音（二）", "sub": "ㅇ ㅈ ㅊ ㅋ ㅌ ㅍ ㅎ", "rows": [K("ㅇㅈㅊㅋ"), K("ㅌㅍㅎ")],
         "notes": ["ㅇ 在字首不發音，當收音念 ng：아、앙。", "ㅊ ㅋ ㅌ ㅍ 是「激音」：比 ㅈ ㄱ ㄷ ㅂ 多一筆，要用力送出一口氣。",
                   "十四個基本子音：ㄱ ㄴ ㄷ ㄹ ㅁ ㅂ ㅅ ㅇ ㅈ ㅊ ㅋ ㅌ ㅍ ㅎ（字典順序）。"]},
        {"id": "c3", "title": "硬音（雙子音）", "sub": "ㄲ ㄸ ㅃ ㅆ ㅉ", "rows": [K("ㄲㄸㅃ"), K("ㅆㅉ")],
         "notes": ["兩個一樣的子音疊在一起＝硬音：喉嚨用力、不送氣，聲音短而緊。", "台灣人可以想成「很用力、不吐氣的 ㄍ ㄉ ㄅ」：까（kka）、빵（麵包）、싸다（便宜）。"]},
        {"id": "c4", "title": "平音・激音・硬音", "sub": "가 카 까 對照聽", "kind": "pairs", "tip": "點一下聽，比較每一列的平音、激音、硬音。",
         "rows": [triple("ㄱㅋㄲ"), triple("ㄷㅌㄸ"), triple("ㅂㅍㅃ"), triple("ㅈㅊㅉ"), triple("ㅅㅆ")],
         "notes": ["韓文聽力最難的地方：同一組子音有三種念法。", "平音（가）：輕輕的、稍微送氣；激音（카）：用力送出一大口氣；硬音（까）：喉嚨繃緊、完全不送氣。",
                   "拿一張紙放在嘴前：念激音紙會被吹動，念硬音幾乎不動。"]},
    ]
    lessons2 = [
        {"id": "v3", "title": "複合母音（一）", "sub": "ㅐ ㅔ ㅒ ㅖ", "rows": [V("ㅐㅔ"), V("ㅒㅖ")],
         "notes": ["ㅐ（ㅏ＋ㅣ）和 ㅔ（ㅓ＋ㅣ）現在的首爾話幾乎同音，都像 ㄝ；寫法要分清楚。", "ㅒ、ㅖ 是前面加「ㄧ」：예（是）、얘기（話題）。"]},
        {"id": "v4", "title": "複合母音（二）", "sub": "ㅘ ㅙ ㅚ ㅝ ㅞ ㅟ ㅢ", "rows": [V("ㅘㅙㅚㅝ"), V("ㅞㅟㅢ")],
         "notes": ["ㅗ 開頭的配 ㅏ ㅐ ㅣ（ㅘ ㅙ ㅚ），ㅜ 開頭的配 ㅓ ㅔ ㅣ（ㅝ ㅞ ㅟ）。", "ㅙ、ㅚ、ㅞ 三個現在聽起來幾乎一樣：왜（為什麼）、회사（公司）、웨이터（服務生）。",
                   "ㅢ：字首念 ㅡ＋ㅣ（의사 醫生）、在字中常念 ㅣ（희망）、當「的」念 ㅔ。", "到這裡，四十音（母音 21＋子音 19）都學完了。"]},
        {"id": "f1", "title": "收音（받침）", "sub": "七個代表音", "rows": [[final(c, ex) for c in "ㄱㄴㄷㄹ"], [final(c, ex) for c in "ㅁㅂㅇ"]],
         "notes": ["方塊字最下面的子音叫收音（받침）。收音寫法很多，但念出來只有七種：ㄱ ㄴ ㄷ ㄹ ㅁ ㅂ ㅇ。",
                   "ㄱ ㄷ ㅂ 收尾時嘴巴擺好位置就停住、不把音爆出來，像台語的入聲：학（學）、옷（衣服，念 옫）、밥（飯）。",
                   "收音後面接 ㅇ 開頭的字，收音會移過去念：한국어＝한구거、음악＝으막（字卡上的［唸法］會標出來）。"]},
    ]
    def cr(chars):
        return [[{"ch": c, "roma": (VOWELS.get(c) or CONS.get(c))[0], "a": (vowel(c, ex) if c in VOWELS else cons(c, ex))["a"]} for c in row] for row in chars]
    chart = {"tabs": [
        {"title": "母音", "sections": [{"title": "基本母音 10", "rows": cr(["ㅏㅑㅓㅕㅗ", "ㅛㅜㅠㅡㅣ"])},
                                     {"title": "複合母音 11", "rows": cr(["ㅐㅒㅔㅖ", "ㅘㅙㅚㅝ", "ㅞㅟㅢ"])}]},
        {"title": "子音", "sections": [{"title": "基本子音 14", "rows": cr(["ㄱㄴㄷㄹㅁ", "ㅂㅅㅇㅈㅊ", "ㅋㅌㅍㅎ"])},
                                     {"title": "硬音 5", "rows": cr(["ㄲㄸㅃㅆㅉ"])}]},
        {"title": "收音", "sections": [{"title": "七個代表音", "rows": [[{"ch": FINALS[c][0], "roma": FINALS[c][1], "a": f"l/f-{FINALS[c][1].lstrip('-')}"} for c in "ㄱㄴㄷㄹ"],
                                                                    [{"ch": FINALS[c][0], "roma": FINALS[c][1], "a": f"l/f-{FINALS[c][1].lstrip('-')}"} for c in "ㅁㅂㅇ"]]}]},
    ]}
    data = {"kind": "hangul", "title": "四十音", "lang": "ko", "sub": "母音・子音・收音 9 課", "chartTitle": "四十音表",
            "intro": "韓文的字母叫「韓字（한글）」：母音 21 個、子音 19 個，合稱四十音。子音＋母音（＋收音）拼成一個方塊字，學會拼法就能念出所有韓文。每課先看表、點一下聽，再做練習。",
            "groups": [{"title": "母音與子音", "lessons": lessons1}, {"title": "複合母音與收音", "lessons": lessons2}], "chart": chart}
    with open(os.path.join(ROOT, "data", "letters.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    seen, uniq = set(), []
    for t in TTS:
        if t["file"] not in seen:
            seen.add(t["file"]); uniq.append(t)
    os.makedirs(os.path.join(WORK, "build"), exist_ok=True)
    with open(os.path.join(WORK, "build", "letters_tts.json"), "w", encoding="utf-8") as f:
        json.dump(uniq, f, ensure_ascii=False, indent=0)
    cells = [c for g in data["groups"] for l in g["lessons"] for row in l["rows"] for c in row if c]
    print(f"{sum(len(g['lessons']) for g in data['groups'])} 課、{len(cells)} 格（有例字 {sum(1 for c in cells if c.get('ex'))}）、音檔 {len(uniq)} 個")


if __name__ == "__main__":
    main()
