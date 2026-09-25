"""主題（路線）定義：代碼、名稱、路線色，以及由路線色推算的色場、文字與線條色。
韓文版（2026-09-25）：沿用旅ことば的八個家族與色票；主題改成韓國版，另加烤肉炸雞、醫美、韓服拍照、追星四條。"""

# 色票（2026-09-24 使用者指定：到 colormind.io/bootstrap 選幾組，同組色票用在同性質的單元）。
# 2026-09-24 再改：底色一律米色，色票只當點綴（線、站點、按鈕），不再整片鋪色。
# 用 Colormind「ui」模型（Bootstrap 頁面同一個模型）產生，主色鎖定為先前選定的寶石灰調，
# 其餘四色由 Colormind 配；每類產生 8 組後依條件評分挑選（workspace/palette/colormind/）。
# 每組五色：淺底 LS、淺強調 LA、主色 M、深強調 DA、深字 DS。
PALETTES = {
    "basic": ["#f6f3f1", "#a88783", "#705d4e", "#827c98", "#1c1920"],   # 2026-09-24 改暖墨色（使用者不要藍色）
    "move": ["#f6eff4", "#55bbd0", "#167793", "#777b67", "#1a1b25"],
    "stay": ["#fbf9fa", "#9c8c98", "#9a526c", "#827487", "#232027"],
    "food": ["#f4f7f4", "#8a8ea2", "#a4613a", "#b44153", "#221620"],
    "shop": ["#fbf9fa", "#948b9a", "#875a93", "#7d7287", "#211e25"],
    "care": ["#f5f4f1", "#d69265", "#9c534c", "#bb7297", "#27242e"],
    "city": ["#e7ebdb", "#7dae90", "#367d5b", "#658087", "#1d1f23"],
    "listen": ["#f5f4f4", "#91a3bf", "#6e61a0", "#777c9c", "#282c3e"],
}
ROLE = {"LS": 0, "LA": 1, "M": 2, "DA": 3, "DS": 4}
# 每條路線用所屬色票的哪個顏色（M+DA 表示兩色中間）
ASSIGN = {
    "GR": ("basic", "M"), "VB": ("basic", "DA"), "NM": ("basic", "LA"),
    "AP": ("move", "M"), "TR": ("move", "LA"), "BT": ("move", "DA"), "DR": ("move", "M+DA"), "DI": ("move", "M+LA"),
    "HT": ("stay", "M"), "ON": ("stay", "DA"),
    "FD": ("food", "M"), "RS": ("food", "DA"), "DK": ("food", "LA"), "BB": ("food", "M+DA"),
    "SH": ("shop", "M"), "CV": ("shop", "DA"), "DS": ("shop", "LA"),
    "EM": ("care", "M"), "MD": ("care", "LA"), "DM": ("care", "DA"),
    "SG": ("city", "M"), "SN": ("city", "DA"), "SV": ("city", "LA"), "HB": ("city", "M+LA"), "KP": ("city", "M+DA"),
    "LS": ("listen", "M"),
}

# (id, 中文名稱, 韓文路線名)；名稱用直白的說法（旅ことば時使用者覺得「聽懂對方說的話」莫名其妙）
# 2026-09-25 韓文版：溫泉→汗蒸幕與澡堂、電車→地鐵與交通卡、藥妝→美妝保養、飲料甜點→咖啡廳與點餐機；
# 使用者另外要了烤肉與炸雞、醫美與皮膚科、韓服與拍照打卡、追星與演唱會；自駕保留但縮小（濟州島）
THEMES = [
    ("GR", "寒暄與應答", "인사"),
    ("NM", "數字・時間・價錢", "숫자"),
    ("AP", "機場與入境", "공항"),
    ("TR", "地鐵與交通卡", "지하철"),
    ("BT", "巴士與計程車", "버스·택시"),
    ("DR", "自駕與加油", "드라이브"),
    ("DI", "問路與方向", "길 찾기"),
    ("HT", "飯店住宿", "숙소"),
    ("ON", "汗蒸幕與澡堂", "찜질방"),
    ("RS", "餐廳點餐", "식당"),
    ("BB", "烤肉與炸雞", "고기·치킨"),
    ("FD", "料理與食材", "음식"),
    ("DK", "咖啡廳與點餐機", "카페"),
    ("SH", "購物與結帳", "쇼핑"),
    ("CV", "便利商店", "편의점"),
    ("DS", "美妝保養", "화장품"),
    ("MD", "看醫生", "병원"),
    ("EM", "緊急求助", "긴급"),
    ("DM", "醫美與皮膚科", "피부과"),
    ("SG", "觀光景點", "관광"),
    ("SN", "招牌與標示", "표지판"),
    ("SV", "網路・領錢・天氣", "생활"),
    ("HB", "韓服與拍照打卡", "한복·사진"),
    ("KP", "追星與演唱會", "케이팝"),
    ("LS", "店員與廣播常說的話", "듣기"),
    ("VB", "常用動詞與形容詞", "기본 단어"),
]


N1 = "#f9f9f7"   # 淺色模式底：2026-09-25 使用者指定的色票（旅ことば是 #f7f5f0）；線與字的對比依它推算
N9 = "#1c1814"   # 深色模式底／深色文字（深咖啡）
N8 = "#29241e"   # 深色模式的卡片面


def _rgb(h):
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c * 255))):02x}" for c in rgb)


def _lum(rgb):
    def ch(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _mix(a, b, t):
    """a 往 b 混 t（0..1）"""
    return [x + (y - x) * t for x, y in zip(a, b)]


def _toward(color, target, against, need):
    """把 color 往 target 推，直到與 against 的對比 ≥ need"""
    c = color
    for i in range(0, 101):
        c = _mix(color, target, i / 100)
        if contrast(c, against) >= need:
            break
    return c


def _alpha_for(ink, field, need, start=0.72):
    """ink 疊在 field 上最低要多少不透明度才達到 need 對比"""
    a = start
    while a < 1.0:
        if contrast(_mix(field, ink, a), field) >= need:
            return round(a, 2)
        a += 0.02
    return 1.0


def _pick(fam, role):
    pal = [_rgb(c) for c in PALETTES[fam]]
    if "+" in role:
        a, b = role.split("+")
        return _mix(pal[ROLE[a]], pal[ROLE[b]], 0.5)
    return pal[ROLE[role]]


def theme_list():
    white, n9, n1, n8 = [1, 1, 1], _rgb(N9), _rgb(N1), _rgb(N8)
    out = []
    for tid, name, ko in THEMES:
        fam, role = ASSIGN[tid]
        pal = PALETTES[fam]
        # 同一家族的主題一律用家族主色 M（顏色＝分類，首頁家族色塊和下一站卡片才對得上；旅ことば 2026-09-25 定案）
        c = _pick(fam, "M")
        dark = _rgb(pal[4])
        # 色場文字：白字或該色票的深字，取對比高者；都不到 4.5 就把色場往深字方向壓到白字過關
        cw, cd = contrast(c, white), contrast(c, dark)
        if max(cw, cd) >= 4.5:
            field, ink = c, (white if cw >= cd else dark)
        else:
            field, ink = _toward(c, dark, white, 4.5), white
        ink_rgb = ", ".join(str(round(x * 255)) for x in ink)
        a2 = _alpha_for(ink, field, 4.5)
        out.append({
            "id": tid, "code": tid, "name": name, "ko": ko, "family": fam,
            "color": _hex(c),
            "field": _hex(field),
            "on": _hex(ink),
            "on2": f"rgba({ink_rgb}, {a2})",
            "on3": f"rgba({ink_rgb}, 0.34)",
            "veil": f"rgba({ink_rgb}, {0.18 if ink == white else 0.1})",
            # 色場畫面裡的卡片：該色票的淺底與深字
            "paper": pal[0], "ink": pal[4],
            # 畫在淺底／深底上的線（非文字 ≥3:1）與文字（≥4.5:1）
            "lL": _hex(_toward(c, n9, n1, 3.0)),
            "lD": _hex(_toward(c, white, n9, 3.0)),
            "tL": _hex(_toward(c, n9, n1, 4.5)),
            "tD": _hex(_toward(c, white, n9, 4.5)),
            # 淡彩（首頁的下一站卡片）：白上 12% 的主題色、深色模式卡片面上 18%
            "bgL": _hex(_mix(white, c, 0.12)),
            "bgD": _hex(_mix(n8, c, 0.18)),
        })
    return out


THEME_IDS = [t[0] for t in THEMES]

# 首頁的主題家族分類（2026-09-25 使用者要求：首頁改依主題分類、以顏色區分）；
# 每個家族用色票主色（ASSIGN 裡 role 是 M 的主題）當代表色
FAMILY_NAMES = [("basic", "基本"), ("move", "交通"), ("stay", "住宿"), ("food", "飲食"), ("shop", "購物"),
                ("care", "醫療緊急"), ("city", "觀光生活"), ("listen", "店員廣播")]


def family_list():
    rep = {fam: tid for tid, (fam, role) in ASSIGN.items() if role == "M"}
    return [{"id": f, "name": n, "rep": rep[f]} for f, n in FAMILY_NAMES]

if __name__ == "__main__":
    for t in theme_list():
        print(t["id"], t["family"], "field", t["field"], "on", t["on"], t["on2"], "paper", t["paper"], "ink", t["ink"], "| lL", t["lL"], "lD", t["lD"])
