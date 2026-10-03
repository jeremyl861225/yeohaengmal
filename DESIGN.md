---
name: 여행말
description: 在韓國旅行用的單字路線 App（旅ことば系列）：ShaderGradient 的漸層波面上浮著液態玻璃，明朝體的字是主角。
colors:
  ink: "#2a1a2e"
  ink-2: "#57405a"
  ink-3: "#7a6580"
  glass: "rgb(255 255 255 / 0.42)"
  glass-2: "rgb(255 255 255 / 0.28)"
  glass-3: "rgb(255 255 255 / 0.7)"
  edge: "rgb(255 255 255 / 0.66)"
  edge-2: "rgb(255 255 255 / 0.36)"
  hair: "rgb(42 26 46 / 0.1)"
  track: "rgb(42 26 46 / 0.14)"
  cta: "#2a1a2e"
  cta-ink: "#ffffff"
  ok: "#1d7748"
  ng: "#b1372f"
  gold: "#a86a07"
  badge: "#edb83a"
  sky-base: "#e9c8b4"
  halo-1: "#ff5005"
  halo-2: "#dbba95"
  halo-3: "#d0bce1"
  dusk-ink: "#fff6fb"
  dusk-ink-2: "#ead7ee"
  dusk-ink-3: "#bba4c6"
  dusk-glass: "rgb(26 8 58 / 0.44)"
  dusk-sky-base: "#140a2e"
  universe-1: "#5606ff"
  universe-2: "#fe8989"
  universe-3: "#000000"
  fam-basic: "#5348a1"
  fam-move: "#197cb3"
  fam-stay: "#bd8c1d"
  fam-food: "#d76900"
  fam-shop: "#c84d83"
  fam-care: "#c73335"
  fam-city: "#038c70"
  fam-listen: "#924598"
typography:
  display:
    fontFamily: "Yeohaengmal Serif (Noto Serif KR subset), Noto Serif KR, AppleMyungjo, Nanum Myeongjo, Batang, serif"
    fontSize: "clamp(32px, 18vw, 72px)"
    fontWeight: 900
    lineHeight: 1.3
    letterSpacing: "0.02em"
  headline:
    fontFamily: "Zen Old Mincho, Yeohaengmal Serif, Hiragino Mincho ProN, Songti TC, Noto Serif TC, serif"
    fontSize: "40px"
    fontWeight: 900
    lineHeight: 1.2
    letterSpacing: "0.02em"
  title:
    fontFamily: "Zen Old Mincho, Yeohaengmal Serif, Hiragino Mincho ProN, Songti TC, Noto Serif TC, serif"
    fontSize: "23px"
    fontWeight: 900
  body:
    fontFamily: "Songti TC, Noto Serif TC, Noto Serif CJK TC, Source Han Serif TC, PMingLiU, serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "tnum"
  label:
    fontFamily: "Zen Old Mincho, Yeohaengmal Serif, Hiragino Mincho ProN, Songti TC, serif"
    fontSize: "12.5px"
    fontWeight: 500
rounded:
  tile: "20px"
  fam: "18px"
  panel: "26px"
  card: "30px"
  pill: "999px"
spacing:
  gutter: "18px"
  panel-pad: "18px"
  grid-gap: "8px"
  tabbar-h: "64px"
components:
  button-primary:
    backgroundColor: "{colors.cta}"
    textColor: "{colors.cta-ink}"
    rounded: "{rounded.pill}"
    padding: "0 22px"
    height: "52px"
  button-ghost:
    backgroundColor: "{colors.glass}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "0 22px"
    height: "52px"
  panel:
    backgroundColor: "{colors.glass}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "18px"
  card-face:
    backgroundColor: "{colors.glass}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "30px 16px 22px"
  chip:
    backgroundColor: "{colors.glass-2}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "0 15px"
    height: "38px"
  chip-selected:
    backgroundColor: "{colors.cta}"
    textColor: "{colors.cta-ink}"
    rounded: "{rounded.pill}"
  family-tile:
    backgroundColor: "{colors.glass-2}"
    textColor: "{colors.ink}"
    rounded: "{rounded.fam}"
    padding: "6px 4px"
  search-field:
    backgroundColor: "{colors.glass-3}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
  tabbar:
    backgroundColor: "{colors.glass}"
    textColor: "{colors.ink-3}"
    height: "64px"
---

# Design System: 여행말

旅ことば（日文版）的「暮色玻璃」系統的韓文版，2026-10-02 照搬。版面、元件、互動、動態與規則都跟 `../tabi-kotoba/DESIGN.md` 一樣；這份只寫韓文版不同的地方，相同的部分簡述。

## Overview

**Creative North Star: "ShaderGradient 的玻璃（同一片玻璃，換一片天）"**

背景是一片慢慢起伏的漸層波面，配色直接取自 ShaderGradient 的預設：淺色模式是 **Halo**（橘、沙、淡紫），深色模式是 **Universe**（電光紫、珊瑚粉、黑）。畫法仿 ShaderGradient 的 plane：雜訊推起的波浪、斜向三色漸層、受光的明暗、一層顆粒。所有內容浮在液態玻璃上，玻璃本身沒有顏色，顏色來自後面的波面。

字是主角：韓文用 Noto Serif KR（500／900 子集），中文標題、數字與小標籤用 Zen Old Mincho（同旅ことば），中文內文用宋體。首頁路線保留首爾地鐵的墨色線號圓與三位數站號（101、201…）。

**Key Characteristics:**
- 兩種表面：ShaderGradient 式漸層波面（WebGL）＋液態玻璃面板
- 韓文 Noto Serif KR、中文標題 Zen Old Mincho、內文宋體
- 墨色（淺色）／月白（深色）按鈕是唯一的實心色塊
- 八個家族色是韓國傳統色，只出現在色點、路線線條、站點與站號章
- 分頁列是有凹口的玻璃板，玻璃珠沉在凹口裡、滾到選中的分頁

## Colors

色彩來自波面；介面只有墨色、玻璃白與八個家族色。比日文版鮮豔，因為 ShaderGradient 的色彩本來就飽和。

### Primary
- **茄紫墨** (ink / cta)：淺色模式的正文與實心按鈕（偏暖的深紫黑，配 Halo 的暖色）。深色模式換成 **月白** (dusk-ink)，按鈕字變成深紫。

### Secondary
- **家族色**（韓國傳統色：fam-basic 쪽빛 藍紫、fam-move 하늘 天空藍、fam-stay 치자 梔子黃、fam-food 주황 朱黃、fam-shop 연지 胭脂粉、fam-care 다홍 大紅、fam-city 청록 青綠、fam-listen 자주 紫朱；OKLCH 亮度 0.46–0.67、彩度 0.11–0.185）：只用在色點、路線線條、站點與站號章的染色。深色模式用 oklch 相對色提亮到 ≥0.74（不支援時 color-mix 混白）。定義在 `tools/themes.py`。

### Tertiary
- **徽章金** (badge)、**對／錯** (ok／ng)：同旅ことば。

### Neutral
- **Halo** (halo-1…3)：淺色波面的三色；sky-base 是瀏覽器頂欄與 PWA 啟動色。
- **Universe** (universe-1…3)：深色波面的三色，亮度壓到 0.74 倍；dusk-sky-base 是頂欄色。
- **玻璃** (glass／glass-2／glass-3)、**玻璃邊** (edge／edge-2)、**髮線與軌道** (hair／track)：同旅ことば；深色模式的面板是深紫玻璃 rgb(26 8 58 / .44)。

### Named Rules
**The 天空上色 Rule.** 介面元件不自己帶底色；要顏色就讓波面透過玻璃。唯一的實心色塊是 CTA 與墨色線號圓。

**The 家族色只當記號 Rule.** 同旅ことば：色點、線條、站點記號、站號章，不鋪大面積、不當正文色。

## Typography

**Display Font:** Noto Serif KR 900（子集 `fonts/ko-serif-900.woff2`，備援 AppleMyungjo、Nanum Myeongjo、Batang）
**Body Font:** Songti TC（中文內文）；韓文例句 Noto Serif KR 500
**Label/Mono Font:** Zen Old Mincho 500／900（中文標題、數字、小標籤；子集只收介面用字）

**Character:** 韓文明朝的粗筆配舊明朝的中文標題，都是有筆鋒的襯線字。漢字詞上方用小字標漢字（宋體）。

### Hierarchy
- **Display** (900, 依字數自動縮放、上限 72px（2026-10-03 使用者嫌太大）, 1.3)：字卡的韓文大字；下方是實際唸法［가치］與羅馬拼音。
- **Headline** (900, 40px, 1.2)：首頁下一站站名。
- **Title** (900, 23px)：路線分級標題；家族名 16px／700。
- **Body** (400, 16px, 1.55)：中文內文；字卡中文意思 24px／600。
- **Label** (500, 11–14px)：編號、站號、羅馬拼音、分頁名稱。

### Named Rules
**The 一行 Rule.** 同旅ことば：標題、副標、站名、字表的單字與中文盡量排成一行（`data-fit`＋`fitText`），縮到最小也放不下就維持原字級、平均換成兩行。

## Layout

同旅ことば：單欄、最大寬 560px、左右 18px；首頁是下一站面板、3×3 家族格、可收合的三條線（每條線前面有墨色線號圓）。字卡頁是可拖曳的玻璃卡面、發音列、例句面板、底部上一張／下一張。

## Elevation & Depth

同旅ことば：深度靠玻璃＋背景模糊（22px、飽和 1.6）、上緣 1px 高光、1px 細邊、淡環境陰影；陰影色偏暖（rgb(70 24 30 / .18)）。

## Shapes

同旅ことば：膠囊按鈕、20／18／26／30px 圓角、站號章 14px、分頁列 32px 圓角板＋凹口。站號是三位數，章裡的數字縮到 18px。

## Components

同旅ことば（按鈕、站號章、標籤、卡面、搜尋列、分頁列、下一站面板）。韓文版另外有：
- **線號圓**：26px 墨色實心圓、Zen Old Mincho 900 的 1／2／3，放在三條線的標題前（首爾地鐵的路線標誌，不另加顏色）。
- **實際唸法列**：字卡大字下方，［唸法］用 Noto Serif KR 20px、羅馬拼音 16px。
- **開場**：約 1.7 秒，夜色亮成 Halo（深色模式成 Universe），一團暖光升起，玻璃磚上浮出「旅」，下面是「여행말」；之後 App 淡入在同一片天空上。點一下跳過；減少動態效果時不播。

### 課程與專欄（2026-10-02）
- **入口格**：首頁「下一站」下面一排 glass-2 小格（圓角 20px），左邊 44px 的玻璃方塊放一個代表字（가，Zen Old Mincho／Noto Serif KR 900），右邊標題＋學完幾課。
- **字母格**：五十音／四十音的課與全表，glass-2 小磚（圓角 14px）、字 28px、下面拼音 12px；點一下播音、選中的格加 2px 墨色內框，下面跳出說明卡（例字、注音近似、名稱）。
- **練習**：沿用測驗的選項磚與底部判定卡；答對 0.75 秒自動換題，答錯才出現「下一題」。
- **圖示**：背景就是 App 的天空著色器（ShaderGradient Halo）算出來再柔化，中央一個墨色的字（「여」，旅的韓文音讀）；沒有其他圖形。`tools/make_icons.py`。

### 文法專欄（2026-10-03）
- **課程表**：沿用四十音的課程表（`lt-row`：序號圓、標題、副標、學完／下一課），分五組：句子的骨架、助詞、動詞與形容詞的變化、旅行必備句型、指示・疑問・數字。標題裡的韓文字一律用韓文明朝體。
- **一課的版面**（由上到下）：標題與副標 → 玻璃面板（一句重點＋公式小膠囊 `gm-chip`）→ 說明面板（15px、行高 1.85、**粗體**標重點）→ 變化表（`gm-table`，12px 灰色表頭、列與列之間細線）→ 例句面板 → 小提醒 → 底部「練習這一課／下一課」。
- **例句**：韓文 19px（Noto Serif KR 500）、下面一行中文；這課要教的文法部分用粗體加下半截金色底線（`gm-ko em`，深色模式自動變亮金）；整列可以點，右邊是播放鈕。
- **練習**：沿用測驗的選項磚與底部判定卡。三種題型——填空（空格是 2.4em 的底線，答完填入綠色正解）、選出正確的句子、聽句子選意思；答對 1.3 秒（聽力 0.75 秒）自動換題並把整句念一次，答錯判定卡會顯示正解句、念一次、並寫出為什麼（`why`）。
- 內容與音檔：`tools/grammar/*.py` 手寫 → `tools/build_grammar.py` 檢查並產生 `data/grammar.json`；音檔名是朗讀文字的雜湊（`audio/g/`），改句子就換網址。

## Do's and Don'ts

### Do:
- **Do** 跟著旅ことば的 DESIGN.md 走；兩邊的元件與規則保持一致，改一邊就改另一邊。
- **Do** 天空只用 ShaderGradient 的 Halo／Universe 三色；要換色組先問使用者。
- **Do** 韓文一律用打包的 Noto Serif KR；資料或介面文字改了要重跑 `tools/make_font.py`。

### Don't:
- **Don't** 回到米色紙與平面卡片清單的舊外觀（2026-10-02 起淘汰）。
- **Don't** 在 UI 用系統無襯線字；不要讓韓文退回黑體。
- **Don't** 用家族色鋪大面積或當正文色。
- **Don't** 讓動畫一直重畫（流光邊只繞一圈；天空每秒最多 10 格）。
