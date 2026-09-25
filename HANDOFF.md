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
| 外觀 | 沿用旅ことば；路線改首爾地鐵風：線號圓（1 藍、2 綠、3 橘）＋三位數站號（101、201…） |
| 聲音 | **待定**：試聽檔在 iCloud 雲碟「韓文聲音試聽」；韓文只有 SunHi 一個女聲，男聲 InJoon 或 Hyunsu。樣本暫用 SunHi＋InJoon |
| 圖示 | **待定**：候選 A「여행」（Noto Serif KR 粗體，目前用這個）、B「旅行」（同日文版）、C「여」，在工作區 `icon-candidates/` |
| 開場 | 太極的紅藍圓＋米色「旅」（日文版是日の丸紅圓）——**還沒給使用者看過** |

## 進度

- [x] 需求訪談（兩輪）、聲音試聽檔
- [x] App 外殼：複製旅ことば並改名（localStorage `yeohaengmal/v1`、快取 `yeohaengmal-v1`／`yeohaengmal-audio`、備份 `app: yeohaengmal`）
- [x] 韓文專用：漢字標記 `{공항|空港}`、實際唸法＋羅馬拼音顯示、搜尋（相容字母前綴、初聲、拼音、漢字、中文）、音節方塊拼字題、看韓文選實際唸法題、首爾地鐵式站號、太極開場、Noto Serif KR 子集字型
- [x] 30 張樣本（`workspace/.../make_sample.py`，漢字與唸法對過 KRDict）＋樣本發音
- [ ] 來源蒐集（兩個代理進行中，編號 zh/en/ko-01～19 與 21～39）
- [ ] 正規化 → 選字 → 排名分課 → 撰寫 → build_data（qa 清到 0）→ 發音 → 字典 → e2e → 上線

## 工具（已改成韓文版的）

| 程式 | 作用 |
|---|---|
| `tools/pipeline/krdict.py` | KRDict XML → `build/krdict.json`（5.4 萬詞；30000.xml 屬性值有沒跳脫的 `<`，已處理） |
| `tools/pipeline/rr.py` | 官方羅馬拼音：子音照唸法、母音照寫法、不標緊音化（korean-romanizer 會拼錯，不要用） |
| `tools/themes.py` | 26 條主題、八個家族、色票 |
| `tools/make_font.py` | Noto Serif KR 子集 → `fonts/ko-serif.woff2`、`ko-serif-600.woff2`（資料改了要重跑並升 CACHE_VERSION） |
| `tools/make_icons.py` | 圖示（`--text`、`--font` 可做候選） |
| `tools/make_audio.py` | edge-tts 發音（f／m） |

還沒改的：`tools/build_data.py`、`build_dict.py`、`e2e.py`、`pipeline/select.py`、`pipeline/author_prep.py`（日文版原樣，進到該階段再改）。

Python 環境（工作區）：`.venv`（edge-tts、wordfreq[cjk]、kiwipiepy、korean-romanizer、opencc、fonttools、pymupdf、bs4）、
`.venv-g2p`（g2pk2＋python-mecab-ko；和 wordfreq 的 mecab-python3 裝在一起會因為 macOS 檔名不分大小寫而互相蓋掉，所以分開）。

## 若中斷，下一步

看上面第一個未勾的項目。來源代理的產出在工作區 `sources/`（`ls sources/*.json`）。
