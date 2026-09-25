"""國立國語院《韓國語基礎辭典》（KRDict，CC BY-SA 2.0 KR）XML → 精簡索引 build/krdict.json。
每個詞條：{id, w 寫法, hn 同形異義編號, pos 詞性, pron [發音], origin 原語（漢字／外文）, level 初級|中級|高級|없음,
          sem 語義分類, en [英文對譯], ja [日文對譯], def 韓文釋義（第一個）}
2019 年的下載檔**沒有中文對譯**（只有英、日、法、西、阿、蒙、越、泰、印尼、俄），中譯要自己寫。"""
import glob, io, json, os, re, sys
import xml.etree.ElementTree as ET

WORK = os.environ.get("YH_WORK", os.path.expanduser("~/Desktop/Claude code/workspace/work/ko-travel-vocab"))
SRC = os.path.join(WORK, "dict", "krdict")
OUT = os.path.join(WORK, "build", "krdict.json")


def feats(el):
    return {f.get("att"): f.get("val") for f in el.findall("feat")}


def clean(text):
    """30000.xml 的法文對譯在屬性值裡有沒跳脫的 <…>（2019 年版），先把屬性值裡的 < > 與孤立的 & 跳脫"""
    text = re.sub(r'val="([^"]*)"', lambda m: 'val="' + m.group(1).replace("<", "&lt;").replace(">", "&gt;") + '"', text)
    return re.sub(r"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)", "&amp;", text)


def parse_file(path):
    out = []
    with open(path, encoding="utf-8") as f:
        text = clean(f.read())
    for _, el in ET.iterparse(io.StringIO(text), events=("end",)):
        if el.tag != "LexicalEntry":
            continue
        top = feats(el)
        lemma = el.find("Lemma")
        w = feats(lemma).get("writtenForm", "") if lemma is not None else ""
        prons = []
        for wf in el.findall("WordForm"):
            f = feats(wf)
            if f.get("type") == "발음" and f.get("pronunciation"):
                prons.append(f["pronunciation"])
        en, ja, defs = [], [], []
        for sense in el.findall("Sense"):
            sf = feats(sense)
            if sf.get("definition"):
                defs.append(sf["definition"])
            for eq in sense.findall("Equivalent"):
                ef = feats(eq)
                lang, lem = ef.get("language"), (ef.get("lemma") or "").strip()
                if not lem:
                    continue
                if lang == "영어":
                    en.append(lem)
                elif lang == "일본어":
                    ja.append(lem)
        out.append({
            "id": el.get("val") or top.get("id"), "w": w, "hn": int(top.get("homonym_number") or 0),
            "unit": top.get("lexicalUnit", ""), "pos": top.get("partOfSpeech", ""), "pron": prons,
            "origin": top.get("origin", ""), "level": top.get("vocabularyLevel", ""),
            "sem": top.get("semanticCategory", ""), "en": en, "ja": ja, "def": defs[:2],
        })
        el.clear()
    return out


def main():
    entries = []
    files = sorted(glob.glob(os.path.join(SRC, "*.xml")), key=lambda p: int(os.path.basename(p).split(".")[0]))
    for p in files:
        part = parse_file(p)
        entries.extend(part)
        print(os.path.basename(p), len(part), file=sys.stderr)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False)
    print(len(entries), "entries →", OUT)


if __name__ == "__main__":
    main()
