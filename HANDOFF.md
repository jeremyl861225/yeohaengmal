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
| 外觀 | 沿用旅ことば，**配色一律照日文版**（米白底 #f7f5f0、一個家族一個顏色、下一站淡彩；2026-09-25 使用者要求）；路線改首爾地鐵風：墨色線號圓＋三位數站號（101、201…），不另加顏色 |
| 聲音 | **待定**：試聽檔在 iCloud 雲碟「韓文聲音試聽」；韓文只有 SunHi 一個女聲，男聲 InJoon 或 Hyunsu。樣本暫用 SunHi＋InJoon |
| 圖示 | **待定**：候選 A「여행」（Noto Serif KR 粗體，目前用這個）、B「旅行」（同日文版）、C「여」，在工作區 `icon-candidates/` |
| 開場 | 太極的紅藍圓＋米色「旅」（日文版是日の丸紅圓）——**還沒給使用者看過** |

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
- [ ] 等使用者決定：圖示（A 여행 目前用這個／B 旅行／C 여，候選在工作區 `icon-candidates/` 與 iCloud「여행말 圖示候選」）、
      太極開場、男聲（InJoon 或 Hyunsu；改 Hyunsu：`make_audio.py` 的 `VOICES['m']`＋`build_data.py` 的 `VOICE_NAMES`，刪 `build/tts-manifest.json` 裡 audio/m 的紀錄重跑，升 CACHE_VERSION）
- [ ] iPhone 實機：加到主畫面 → 設定頁下載必備線發音 → 飛航模式開一課、播發音、做測驗
- [ ] impeccable 收尾（finish reviewer＋DESIGN.md）

## 工具（已改成韓文版的）

| 程式 | 作用 |
|---|---|
| `tools/pipeline/krdict.py` | KRDict XML → `build/krdict.json`（5.4 萬詞；30000.xml 屬性值有沒跳脫的 `<`，已處理） |
| `tools/pipeline/rr.py` | 官方羅馬拼音：子音照唸法、母音照寫法、不標緊音化（korean-romanizer 會拼錯，不要用） |
| `tools/themes.py` | 26 條主題、八個家族、色票 |
| `tools/make_font.py` | Noto Serif KR 子集 → `fonts/ko-serif.woff2`、`ko-serif-600.woff2`（資料改了要重跑並升 CACHE_VERSION） |
| `tools/make_icons.py` | 圖示（`--text`、`--font` 可做候選） |
| `tools/make_audio.py` | edge-tts 發音（f／m） |

管線（都已改成韓文版）：`pipeline/normalize.py`、`auto_drop.py`、`curate_prep.py`（依優先序切批；`YH_KEEP_IN` 保留進行中的批次）、`auto_curate.py`、`tri2out.py`、`select.py`（主題保底 30、DR 上限 20、`force` 指定收錄）、`author_prep.py`、`g2p_batch.py`；`tools/build_data.py`、`build_dict.py`（離線字典 20,947 詞）、`e2e.py`。

Python 環境（工作區）：`.venv`（edge-tts、wordfreq[cjk]、kiwipiepy、korean-romanizer、opencc、fonttools、pymupdf、bs4）、
`.venv-g2p`（g2pk2＋python-mecab-ko；和 wordfreq 的 mecab-python3 裝在一起會因為 macOS 檔名不分大小寫而互相蓋掉，所以分開）。

## 若中斷，下一步

看上面第一個未勾的項目。來源代理的產出在工作區 `sources/`（`ls sources/*.json`）。
