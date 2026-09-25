"""App 圖示：米色底、墨色襯線大字，下緣一條朱赭色的路線與站點（旅ことば系列的圖示）。
日文版是宋體「旅行」；韓文版預設用 Noto Serif KR 粗體寫「여행」（旅行的韓文），也可以用參數換字與字型做候選：
  python make_icons.py                              # 正式圖示 → icons/
  python make_icons.py --text 旅行 --font songti --out <資料夾>   # 候選
iOS 會自己切圓角，所以輸出滿版方形；maskable 版把內容縮進安全區。字型只用來畫圖示，不隨 App 發佈。"""
from PIL import Image, ImageDraw, ImageFont
import argparse, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get("YH_WORK", os.path.expanduser("~/Desktop/Claude code/workspace/work/ko-travel-vocab"))
FONTS = {
    # 名稱: (檔案, ttc 索引, 可變字型的字重)
    "notokr": (os.path.join(WORK, "fonts", "NotoSerifKR-VF.ttf"), 0, 700),
    "songti": ("/System/Library/Fonts/Supplemental/Songti.ttc", 2, None),   # Songti TC Bold（日文版用的）
    "myungjo": ("/System/Library/Fonts/Supplemental/AppleMyungjo.ttf", 0, None),
}
ap = argparse.ArgumentParser()
ap.add_argument("--text", default="여행")
ap.add_argument("--font", default="notokr", choices=FONTS)
ap.add_argument("--out", default=os.path.join(ROOT, "icons"))
ARGS = ap.parse_args()
OUT = ARGS.out
FONT, FONT_INDEX, WGHT = FONTS[ARGS.font]
TEXT = ARGS.text
GROUND = (0xF5, 0xEF, 0xE3)   # 米色底
INK = (0x1C, 0x18, 0x14)      # 墨色：字與實心站點
LINE = (0x9C, 0x53, 0x4C)     # 朱赭（緊急・求助那組色票的主色）


def draw(size, scale=1.0):
    """先把字與路線畫在透明圖層，量出實際筆畫範圍後整組置中：上下留白等寬、左右留白等寬
    （2026-09-25 使用者要求上下界等寬；原本字的位置是目測，上方留白比下方多約一半）"""
    S = 1024
    k = scale
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = S / 2
    font = ImageFont.truetype(FONT, int((400 if len(TEXT) > 1 else 520) * k), index=FONT_INDEX)
    if WGHT:
        font.set_variation_by_axes([WGHT])
    bb = d.textbbox((0, 0), TEXT, font=font)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    top = c - h / 2 - int(70 * k)
    d.text((c - w / 2 - bb[0], top - bb[1]), TEXT, font=font, fill=INK + (255,))
    # 路線與站點：前兩站實心（已到），最後一站空心（下一站）
    y = c + int(300 * k)
    x0, x1 = c - int(380 * k), c + int(380 * k)
    lw = int(40 * k)
    d.rounded_rectangle([x0, y - lw / 2, x1, y + lw / 2], radius=lw / 2, fill=LINE + (255,))
    r = int(38 * k)
    for i, x in enumerate([x0 + lw / 2, c, x1 - lw / 2]):
        if i < 2:
            d.ellipse([x - r, y - r, x + r, y + r], fill=INK + (255,))
        else:
            d.ellipse([x - r, y - r, x + r, y + r], fill=GROUND + (255,), outline=LINE + (255,), width=int(16 * k))
    group = layer.crop(layer.getbbox())
    img = Image.new("RGB", (S, S), GROUND)
    img.paste(group, ((S - group.width) // 2, (S - group.height) // 2), group)
    return img.resize((size, size), Image.LANCZOS)


os.makedirs(OUT, exist_ok=True)
draw(192).save(os.path.join(OUT, "icon-192.png"))
draw(512).save(os.path.join(OUT, "icon-512.png"))
draw(180).save(os.path.join(OUT, "apple-touch-icon.png"))
draw(512, scale=0.8).save(os.path.join(OUT, "icon-maskable-512.png"))
print("icons written")
