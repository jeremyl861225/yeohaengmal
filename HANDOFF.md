# 여행말 Yeohaengmal — 交接檔

韓國旅遊韓文單字卡 PWA（手機優先、可離線），旅ことば（日文版，`../tabi-kotoba`）的韓文版。
repo：`jeremyl861225/yeohaengmal`（public）。做法照 skill **`travel-vocab-app-builder`**；踩到的新坑回寫 skill。
中間產物（來源詞表、字典、試聽、截圖）在 `~/Desktop/Claude code/workspace/work/ko-travel-vocab/`，不進 repo。

## 已定案的決定（2026-09-25 與使用者確認）

| 項目 | 決定 |
|---|---|
| 名稱 | 여행말 Yeohaengmal，repo `yeohaengmal` |
| 漢字標註 | 漢字詞上方用小字標漢字（공항 上方「空港」），設定可關，預設開 |
| 實際唸法 | 寫法和唸法不同時在字下方標［가치］，預設開 |
| 羅馬拼音 | 官方拼法（RR），**預設顯示**（使用者選的，和日文版不同） |
| 語言特有題型 | 「看韓文選實際唸法」（只出寫法≠唸法的字），共 8 種題型 |
| 旅行型態 | 城市為主（首爾、釜山），濟州島可能自駕 → 自駕主題保留但縮小（約 20 張） |
| 主題 | 日文版 22 條改韓國版（地鐵與交通卡、汗蒸幕與澡堂、美妝保養、咖啡廳與點餐機），加烤肉與炸雞、醫美與皮膚科、韓服與拍照打卡、追星與演唱會，共 26 條（`tools/themes.py`） |
| 字量 | 約 1200（沿用） |
| 外觀 | **2026-10-02 起：旅ことば v22 的「暮色玻璃」＋ShaderGradient 配色**（使用者要求韓文版套日文版新設計、換一套顏色；見下方同日段落與 `DESIGN.md`）。舊紀錄：沿用旅ことば，**配色一律照日文版**（米白底 #f7f5f0、一個家族一個顏色、下一站淡彩；2026-09-25 使用者要求）；路線改首爾地鐵風：墨色線號圓＋三位數站號（101、201…），不另加顏色 |
| 聲音 | **定案：SunHi 女聲＋InJoon 男聲**（2026-09-25 使用者聽過三聲並排的試聽頁後說「利用目前的聲音即可」；另一個男聲 Hyunsu 不用）。試聽頁已撤 |
| 圖示 | **定案：A「여행」**（Noto Serif KR 粗體；2026-09-25 使用者在測試展示站比過 B「旅行」＝跟日文版一模一樣、C「여」後選 A）。候選留在工作區 `icon-candidates/` |
| 開場 | **2026-10-02 起**：夜色亮成 Halo、暖光升起、玻璃磚上的「旅」＋「여행말」（同旅ことば的玻璃開場）。舊紀錄：太極的紅藍圓＋白色「旅」（2026-09-25 定案） |

## 進度

- [x] 需求訪談（兩輪）、聲音試聽檔
- [x] App 外殼：複製旅ことば並改名（localStorage `yeohaengmal/v1`、快取 `yeohaengmal-v1`／`yeohaengmal-audio`、備份 `app: yeohaengmal`）
- [x] 韓文專用：漢字標記 `{공항|空港}`、實際唸法＋羅馬拼音顯示、搜尋（相容字母前綴、初聲、拼音、漢字、中文）、音節方塊拼字題、看韓文選實際唸法題、首爾地鐵式站號、太極開場、Noto Serif KR 子集字型
- [x] 30 張樣本（`workspace/.../make_sample.py`，漢字與唸法對過 KRDict）＋樣本發音
- [x] 來源蒐集：69 份（zh 30、en 27、ko 12）→ 工作區 `sources/`（編號 zh/en/ko-01～19、21～39、40～49 三個代理分段）
- [x] 正規化：5,451 個候選（`build/candidates.json`）；規則剔除 1,099（`build/curate/out-00-auto.json`：冷門菜名、廣播全文、單一來源長句）
- [x] 指定收錄 25 個來源都沒收到的關鍵字（`build/curate/manual.json`，`force: true`：키오스크、택스 리펀드、원 플러스 원、불판、카카오 T、유심…）
- [x] 選字：30 批（01～15 照 RULES.md，16～30 快速分流 TRIAGE.md）＋ `manual.json`（106 條：指定收錄 25、專有地名品牌與樣板句 73 刪除、重複與漢字修正）。
      01 用 Opus，其餘 Sonnet（11:50 撞到用量上限後改的）。
- [x] 排名分課：1,200 張、90 課、300／450／450（`build/selection.json`、`build/ids.json`）。
      主題上限：自駕 20、動詞 60、數字 100（一般學習詞表會灌高動詞）；保底：機場 45，地鐵、住宿、餐廳、購物、店員廣播 40，其餘 30。
- [x] 撰寫：12 批 × 100（Sonnet 代理）＋遞補 7 張（主線程）；人工修正 `build/author/fix.json`（19 條：蔘雞湯、醫美台灣譯名、例句只重寫卡片的 10 條、樣板句）、
      逐條確認的誤報 `build/author/qa_ok.json`。build_data 的 qa 全部清空。
- [x] 課名：`build/unit_names.json`（89 課，全 App 不重複）；必備線從寒暄開始。
- [x] 字型子集重做（777 音節，124 KB）；`CACHE_VERSION` 升到 v2。
- [x] 發音：4,800 檔、53 MB、0 失敗（SunHi＋InJoon；`YH_TTS_CONCURRENCY=12` 約 40 分鐘）
- [x] e2e `--all-cards` 通過（1,200 張、8 種題型都出現、打到一半／初聲／漢字／拼音搜尋、離線快取）
- [x] **2026-09-25 上線** <https://jeremyl861225.github.io/yeohaengmal/>：CORE 17 檔 200、預先快取 17 筆、斷網開卡片與搜尋、快取裡的音檔可播（Chromium 實測）
- [x] 2026-09-25：配色照搬日文版 v10（使用者「配色規則請參考日文單字app」），快取 v3 已上線
- [x] 2026-09-25：底色改成使用者貼的色票 **#f9f9f7**（日文版仍是 #f7f5f0），快取 v4 已上線
- [x] 2026-09-25：單字編號（照學習順序 0001 起，旅ことば v11 同一套邏輯）：**字卡上是單字左上角淡淡的小灰字、不加框**（使用者指定位置），
      字表與搜尋結果在中文前面顯示，搜尋框打編號找卡；快取 v5 已上線
- [x] 2026-09-25：單字編號的呈現**照日文版（旅ことば v12、v13）**（使用者「將單字編號呈現方法比照日文app」）：字卡 `.card-no` 絕對定位在大字左上方、
      卡片上方留 18px 不疊字；課程字表的號碼改成單字編號的淡灰小字、不加圈（看過的換課色），中文前不再重複；搜尋結果 `.r-no` 同色（`--ink-3`＋0.7 透明）。
      e2e 加查字卡編號與課程字表號碼。sw.js 的換頁只對 App 本身回 App 殼（子頁如 `voices/` 直接上網）；快取 v6
- [x] 2026-09-25：使用者的三個決定都回了——聲音維持 SunHi＋InJoon、圖示 A 여행、太極開場可以（都是現況，App 不用改）。
      挑選頁在測試展示站 <https://jeremyl861225.github.io/tabi-kotoba-test/yeohaengmal/2026-09-25-icon-splash/>（已標定案）
- [ ] iPhone 實機：加到主畫面 → 設定頁下載必備線發音 → 飛航模式開一課、播發音、做測驗
- [ ] impeccable 收尾（finish reviewer＋DESIGN.md）

## 2026-10-03：首頁入口格（v9）
- 不能縮放（使用者：日韓 App 都不要支援雙擊或兩指縮放）：同旅ことば v26 的做法（viewport、`touch-action: pan-x pan-y`、擋 gesture 事件與兩指 touchmove）。

- 旅ことば的首頁入口格跑版（說明字溢出），同一套修正照搬：文字欄 `minmax(0, 1fr)` 鎖寬、說明字改短、360px 以下縮小內距。

## 2026-10-02：新圖示「여」、四十音課程（v8）

使用者要求：圖示重做（顏色同 ShaderGradient、取消鐵軌、韓文改成一個字）；新增四十音課程（由我發揮）。
- **圖示**：「여」＝「旅」的韓文音讀（여행＝旅行），和日文版的「旅」成對。`tools/make_icons.py` 用 `js/sky.js` 的著色器（Halo，t＝140）畫背景，中央墨色 Noto Serif KR 900。
  iPhone 要刪掉主畫面捷徑再加一次才會換圖示。
- **四十音**（`#/letters`，首頁入口格；`js/letters.js` 與旅ことば共用，內容在 `data/letters.json`，`tools/build_letters.py` 產生）：
  9 課＝基本母音兩課、基本子音兩課、硬音、平音・激音・硬音對照（가／카／까 聽辨）、複合母音兩課、收音七個代表音；全表分母音、子音、收音。
  每個字母有名稱（기역…）、代表音節、注音近似提示、例字（字卡裡挑）；練習：聽音選字、看字選拼音；對照課的選項優先用同一列。
- **音檔**：`audio/l/` 61 個，SunHi 放慢 30%（`tools/make_extra_audio.py`）；設定頁「離線使用」多一列「四十音」。
- **字型**：`tools/make_font.py` 把 `data/letters.json` 也算進字表（字母 ㄱ ㅏ… 與課程的中文標題）。
- `js/audio.js` 加 `playFile`（旅ことば同一支）。e2e：課程表、點字母出現說明、第一課練習全對會記成學完、首頁入口格顯示學完課數。

## 2026-10-02：套用旅ことば的「暮色玻璃」＋ShaderGradient 配色（v7）

使用者在日文版選了 D 主題＋B 字體（旅ことば v21／v22），要求「將此設計套用在韓文旅遊 app 上，套上另一套顏色（shadergradient）」。
- **天空**：`js/sky.js` 自寫著色器，畫法仿 ShaderGradient 的 plane（雜訊波面、斜向三色漸層、受光明暗、顆粒）；
  淺色＝**Halo**（#ff5005、#dbba95、#d0bce1），深色＝**Universe**（#5606ff、#fe8989、#000，亮度 0.74）。顏色取自 ShaderGradient 原始碼的 presets。
  省電做法同日文版（半解析度、每秒 10 格、捲動時暫停、背景時停、減少動態效果時只畫一格、沒有 WebGL 時 CSS 漸層）。
- **玻璃與元件**：`css/app.css` 由旅ことば v22 的 CSS 產生，再套韓文版的差異（`--ko` 字型、上方漢字、［唸法］、三位數站號、墨色線號圓、字典列、音節方塊）。
  墨色改偏暖的茄紫 #2a1a2e（配 Halo），深色面板是深紫玻璃。
- **家族色**：`tools/themes.py` 換成韓國傳統色（쪽빛 藍紫、하늘 天空藍、치자 梔子黃、주황 朱黃、연지 胭脂粉、다홍 大紅、청록 青綠、자주 紫朱），比日文版鮮豔。
- **字型**：韓文 Noto Serif KR 500／900（131＋95 KB），中文標題與數字 Zen Old Mincho 500／900（只收介面用字，各 226 KB）。舊的 `ko-serif.woff2`／`ko-serif-600.woff2` 刪掉。
- **其他照搬**：分頁列玻璃珠（`js/tabbar.js`）、開場（`js/splash.js`）、玻璃字卡拖曳換卡、站號章玻璃、一行字自動縮字（`fitText`）、課程字表的打勾與「目前」、測驗題型標籤改 `data-qtype`。
- **沒有照搬**（日文版的功能，不是設計）：字典詞頁與字典發音、測驗終點的「下一站」按鈕、依編碼排序。
- e2e：開場選擇器改 `.splash-tile`、題型改讀 `data-qtype`、加分頁列玻璃珠位置檢查；`--all-cards` 通過（1,200 張）。

## 工具（已改成韓文版的）

| 程式 | 作用 |
|---|---|
| `tools/pipeline/krdict.py` | KRDict XML → `build/krdict.json`（5.4 萬詞；30000.xml 屬性值有沒跳脫的 `<`，已處理） |
| `tools/pipeline/rr.py` | 官方羅馬拼音：子音照唸法、母音照寫法、不標緊音化（korean-romanizer 會拼錯，不要用） |
| `tools/themes.py` | 26 條主題、八個家族、色票 |
| `tools/make_font.py` | 字型子集：Noto Serif KR 500／900 → `fonts/ko-serif-500.woff2`、`ko-serif-900.woff2`；Zen Old Mincho（中文標題，只收介面用字）→ `fonts/zenold-500.woff2`、`zenold-900.woff2`（資料或介面文字改了要重跑並升 CACHE_VERSION） |
| `tools/make_icons.py` | 圖示（`--text`、`--font` 可做候選） |
| `tools/make_audio.py` | edge-tts 發音（f／m） |

管線（都已改成韓文版）：`pipeline/normalize.py`、`auto_drop.py`、`curate_prep.py`（依優先序切批；`YH_KEEP_IN` 保留進行中的批次）、`auto_curate.py`、`tri2out.py`、`select.py`（主題保底 30、DR 上限 20、`force` 指定收錄）、`author_prep.py`、`g2p_batch.py`；`tools/build_data.py`、`build_dict.py`（離線字典 20,947 詞）、`e2e.py`。

Python 環境（工作區）：`.venv`（edge-tts、wordfreq[cjk]、kiwipiepy、korean-romanizer、opencc、fonttools、pymupdf、bs4）、
`.venv-g2p`（g2pk2＋python-mecab-ko；和 wordfreq 的 mecab-python3 裝在一起會因為 macOS 檔名不分大小寫而互相蓋掉，所以分開）。

## 若中斷，下一步

看上面第一個未勾的項目。來源代理的產出在工作區 `sources/`（`ls sources/*.json`）。
