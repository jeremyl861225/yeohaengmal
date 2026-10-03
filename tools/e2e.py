"""端對端驗收（手機視窗）：用 Playwright 實際操作 App。

用法：~/.claude/tools/playwright-venv/bin/python tools/e2e.py [http://127.0.0.1:8741/] [--all-cards]
先在 repo 根目錄開本機伺服器：python3 -m http.server 8741 --bind 127.0.0.1（8731 是日文版用的）
"""
import json, os, re, sys, time
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = next((a for a in sys.argv[1:] if a.startswith("http")), "http://127.0.0.1:8741/")
ALL = "--all-cards" in sys.argv
STORE_KEY = "yeohaengmal/v1"
data = json.load(open(os.path.join(ROOT, "data", "cards.json"), encoding="utf-8"))
cards = data["cards"]
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("  ✗", msg)


def main():
    # 音檔齊全（檔案系統）
    missing = [f"{v}/{c['id']}{s}" for c in cards for v in ("f", "m") for s in ("", "x")
               if (s == "" or c.get("ex")) and not os.path.exists(os.path.join(ROOT, "audio", v, f"{c['id']}{s}.mp3"))]
    check(not missing, f"缺音檔 {len(missing)} 個：{missing[:6]}")

    with sync_playwright() as p:
        b = p.chromium.launch()
        # 開場動畫：會自己消失、點一下可以跳過（主要測試用減少動態效果，開場不顯示、不擋點擊）
        sctx = b.new_context(viewport={"width": 375, "height": 740}, is_mobile=True, has_touch=True, service_workers="block")
        sp = sctx.new_page()
        sp.goto(BASE, wait_until="commit")
        sp.wait_for_selector("#splash .splash-tile", state="attached")
        sp.wait_for_function("!document.getElementById('splash')", timeout=4000)
        sp.goto(BASE + "?reload=1#/browse", wait_until="commit")  # 只換 # 後面不會重新載入，開場不會再出現
        sp.wait_for_selector("#splash", state="attached")
        sp.dispatch_event("#splash", "pointerdown")
        sp.wait_for_function("!document.getElementById('splash')", timeout=1500)
        sctx.close()

        ctx = b.new_context(viewport={"width": 375, "height": 740}, device_scale_factor=2, is_mobile=True, has_touch=True, service_workers="block", reduced_motion="reduce")
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(BASE)
        pg.wait_for_selector(".next")
        n_units = pg.eval_on_selector_all(".stn", "els => els.length")
        check(n_units == len(data["units"]), f"首頁課數 {n_units} ≠ {len(data['units'])}")

        # 課名全 App 不重複；主題家族篩選；三條線可收合
        titles = [u["title"] for u in data["units"]]
        check(len(set(titles)) == len(titles), f"課名有重複：{[t for t in set(titles) if titles.count(t) > 1][:5]}")
        fam_of = {t["id"]: t["family"] for t in data["themes"]}
        for f in data.get("families", [])[:3]:
            want = sum(1 for u in data["units"] if fam_of[u["th"]] == f["id"])
            pg.click(f".fam[data-fam='{f['id']}']")
            pg.wait_for_timeout(120)
            got = pg.eval_on_selector_all(".stn", "els => els.length")
            check(got == want, f"主題家族「{f['name']}」篩選後 {got} 站，應為 {want}")
        pg.click(".fam[data-fam='']")
        pg.wait_for_timeout(120)
        was = pg.eval_on_selector("details.tier", "e => e.open")
        pg.click("details.tier > summary")
        pg.wait_for_timeout(120)
        check(pg.eval_on_selector("details.tier", "e => e.open") != was, "點線的標題列沒有收合／展開")

        # 每張卡：沒有橫向溢出、上方漢字數量正確、實際唸法與羅馬拼音有顯示
        sample = cards if ALL else cards[:: max(1, len(cards) // 120)]
        t0 = time.time()
        for c in sample:
            pg.evaluate(f"location.hash = '#/card/{c['id']}'")
            pg.wait_for_selector(".card .word")
            over = pg.evaluate("document.scrollingElement.scrollWidth - window.innerWidth")
            check(over <= 1, f"{c['id']} {c['w']} 橫向溢出 {over}px")
            n_rt = pg.eval_on_selector_all(".card .word rt", "els => els.length")
            check(n_rt == c["w"].count("{"), f"{c['id']} 上方漢字數 {n_rt} ≠ {c['w'].count('{')}")
            plain_w = re.sub(r"\{([^|{}]+)\|[^{}]+\}", r"\1", c["w"]).replace(" ", "")
            want_pr = c["k"] != "p" and c["r"].replace(" ", "") != plain_w
            has_pr = pg.eval_on_selector_all(".card .read .pr", "els => els.length") > 0
            check(has_pr == want_pr, f"{c['id']} 實際唸法顯示={has_pr}，應為 {want_pr}")
            if c.get("rm"):
                check(pg.eval_on_selector_all(".card .read .roma", "els => els.length") == 1, f"{c['id']} 沒有顯示羅馬拼音")
            no = pg.eval_on_selector(".card .card-no", "e => [e.textContent.trim(), e.getBoundingClientRect().bottom]")
            check(no[0] == f"{c['sq']:04d}", f"{c['id']} 字卡左上角編號 {no[0]}，應為 {c['sq']:04d}")
            wtop = pg.eval_on_selector(".card .word", "e => e.getBoundingClientRect().top")
            check(no[1] <= wtop + 1, f"{c['id']} 編號疊到大字（{no[1]:.0f} > {wtop:.0f}）")
            wh = pg.eval_on_selector(".card .word", "e => e.getBoundingClientRect().height")
            fs = pg.eval_on_selector(".card .word", "e => parseFloat(getComputedStyle(e).fontSize)")
            check(wh < fs * 1.35 * 3.2, f"{c['id']} {c['w']} 單字換太多行（高 {wh:.0f}px）")
        print(f"字卡檢查 {len(sample)} 張，{time.time() - t0:.1f}s")

        # 搜尋：韓文、打到一半的韓文（最後一個音節只打初聲）、初聲、上方漢字、羅馬拼音、中文
        target = next((c for c in cards if "{" in c["w"] and c.get("rm") and c["k"] != "p" and len(re.sub(r"[^가-힣]", "", c["w"])) >= 2), cards[0])
        pg.goto(BASE + "#/browse")
        pg.wait_for_selector("#q")
        head = re.sub(r"[^가-힣]", "", re.sub(r"\{([^|{}]+)\|[^{}]+\}", r"\1", target["w"]))
        CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
        cho = lambda ch: CHO[(ord(ch) - 0xAC00) // 588]
        hanja = "".join(re.findall(r"\|([^{}]+)\}", target["w"]))
        partial = head[:-1] + cho(head[-1])
        for q in (head, partial, "".join(cho(ch) for ch in head), hanja, target["rm"], target["zh"].split("；")[0].split("、")[0]):
            pg.fill("#q", q)
            pg.wait_for_timeout(150)
            ids = pg.eval_on_selector_all(".row", "els => els.map(e => e.getAttribute('href'))")
            check(f"#/card/{target['id']}" in ids, f"搜尋「{q}」找不到 {target['id']}")

        # 編號：照學習順序 1..N 不重複；搜尋框輸入編號找得到那張卡
        sqs = sorted(c.get("sq", 0) for c in cards)
        check(sqs == list(range(1, len(cards) + 1)), "單字編號不是 1..N 連續不重複")
        pick = next(c for c in cards if c.get("sq") == 1)
        pg.fill("#q", "0001")
        pg.wait_for_timeout(150)
        ids = pg.eval_on_selector_all(".row", "els => els.map(e => e.getAttribute('href'))")
        check(ids == [f"#/card/{pick['id']}"], f"搜尋編號 0001 應只找到 {pick['id']}，實際 {ids[:3]}")
        pg.fill("#q", "")
        pg.wait_for_timeout(150)

        # 篩選標籤列：捲到右邊再點，列表不能跳回最前面
        pg.evaluate("document.querySelectorAll('.chips')[1].scrollLeft = 400")
        x0 = pg.evaluate("document.querySelectorAll('.chips')[1].scrollLeft")
        pg.evaluate("""(() => { const row = document.querySelectorAll('.chips')[1]; const box = row.getBoundingClientRect();
            [...row.querySelectorAll('[data-f-th]')].find((b) => { const r = b.getBoundingClientRect(); return r.left > box.left + 4 && r.right < box.right - 4; }).click(); })()""")
        pg.wait_for_timeout(200)
        x1 = pg.evaluate("document.querySelectorAll('.chips')[1].scrollLeft")
        check(x0 > 0 and abs(x1 - x0) < 40, f"點主題標籤後標籤列跳動：{x0} → {x1}")
        pg.click("[data-f-th='']")

        # 測驗：第一課全部作答到終點（先看課程字表的號碼是單字編號、不加圈）
        u = data["units"][0]
        pg.goto(BASE + f"#/unit/{u['id']}")
        pg.wait_for_selector(".word-row .idx")
        sq_of = {c["id"]: c["sq"] for c in cards}
        idx = pg.eval_on_selector_all(".word-row .idx", "els => els.map(e => e.firstChild.textContent.trim())")   # 只讀號碼（後面可能有「目前」標記）
        check(idx == [f"{sq_of[i]:04d}" for i in u["cards"]], f"課程字表的號碼不是單字編號：{idx[:3]}")
        check(pg.eval_on_selector(".word-row .idx", "e => getComputedStyle(e).borderRadius") in ("0px", ""), "課程字表的號碼還有圓圈")
        pg.click("[data-unit-quiz]")
        kinds = set()
        for i in range(len(u["cards"])):
            pg.wait_for_selector("[data-choice], [data-tile]")
            kinds.add(pg.get_attribute(".stage[data-qtype]", "data-qtype"))   # 題型標籤（q-kind）2026-10-02 拿掉了，改讀屬性
            if pg.query_selector("[data-tile]"):
                # 拼音題：依序點方塊直到填滿（不管對錯），確認會自動判分
                while pg.query_selector(".bank [data-tile]:not([disabled])") and not pg.query_selector("[data-quiz-next]"):
                    pg.click(".bank [data-tile]:not([disabled])")
            else:
                pg.click("[data-choice='0']")
            pg.click("[data-quiz-next]")
        print("出現的題型：", "、".join(sorted(kinds)))
        check(len(kinds) >= min(4, len(u["cards"])), f"單元測驗題型太少：{kinds}")
        pg.wait_for_selector(".score")
        check("/" in pg.inner_text(".score"), "測驗沒有到終點")

        # 分頁列：玻璃珠停在目前分頁的正上方，底板凹口跟著它（旅ことば 2026-09-29 的做法，2026-10-02 照搬）
        pg.goto(BASE + "#/")
        pg.wait_for_selector(".next")
        for tab in ("quiz", "settings", "home"):
            pg.click(f".tab[data-tab='{tab}']")
            pg.wait_for_timeout(80)
            dx = pg.evaluate(f"""(() => {{ const b = document.querySelector('.tb-ball').getBoundingClientRect();
                const t = document.querySelector(".tab[data-tab='{tab}'] svg").getBoundingClientRect();
                return Math.abs((b.left + b.width / 2) - (t.left + t.width / 2)) + Math.abs((b.top + b.height / 2) - (t.top + t.height / 2)); }})()""")
            check(dx < 3, f"分頁列的球沒有停在「{tab}」上（差 {dx:.1f}px）")
            check(pg.get_attribute(f".tab[data-tab='{tab}']", "aria-current") == "page", f"分頁「{tab}」沒有標成目前")

        # 星號與不熟清單
        pg.goto(BASE + f"#/card/{cards[1]['id']}")
        pg.wait_for_selector(".topbar .star-btn")
        pg.click(".topbar .star-btn")
        pg.goto(BASE + "#/starred")
        pg.wait_for_selector(".row, .empty")
        check(pg.eval_on_selector_all(".row", "els => els.length") >= 1, "加星後不熟清單是空的")
        badge = pg.inner_text(".tab[data-tab='starred'] .badge-n")
        check(badge.strip() != "" and badge.strip() != "0", "分頁上的不熟數字沒更新")

        # 設定：關掉漢字標註
        pg.goto(BASE + "#/settings")
        pg.click("[data-set-bool='hanja']")
        pg.goto(BASE + f"#/card/{target['id']}")
        pg.wait_for_selector(".card .word rt", state="attached")
        vis = pg.eval_on_selector(".card .word rt", "e => getComputedStyle(e).visibility")
        check(vis == "hidden", "設定關掉漢字標註後仍看得到漢字")
        # 字母課程（五十音／四十音，2026-10-02）：課程表、點字母出現說明、練習全對會記成「學完」
        letters = json.load(open(os.path.join(ROOT, "data", "letters.json"), encoding="utf-8"))
        all_l = [l for g in letters["groups"] for l in g["lessons"]]
        miss = [c["a"] for l in all_l for row in l["rows"] for c in row if c and not os.path.exists(os.path.join(ROOT, "audio", c["a"] + ".mp3"))]
        check(not miss, f"課程音檔缺 {len(miss)} 個：{miss[:5]}")
        first = all_l[0]
        pg.goto(BASE + "#/letters")
        pg.wait_for_selector(".lt-row")
        check(pg.eval_on_selector_all(".lt-row", "els => els.length") == len(all_l), "課程表的課數不對")
        pg.goto(BASE + f"#/letters/{first['id']}")
        pg.wait_for_selector(".lt-cell[data-lt-i]")
        pg.click(".lt-cell[data-lt-i='0']")
        pg.wait_for_selector("#lt-detail .lt-ex")
        cells = [c for row in first["rows"] for c in row if c]
        by_audio = {c["a"]: c for c in cells}
        pg.goto(BASE + f"#/letters/{first['id']}/practice")
        for _ in range(40):
            pg.wait_for_selector("[data-lt-pick]:not([disabled]), .terminal")
            if pg.query_selector(".terminal"):
                break
            t = pg.get_attribute(".stage", "data-lt-type")
            opts = pg.eval_on_selector_all("[data-lt-pick]", "els => els.map(e => e.textContent.trim())")
            if t == "listen":
                want = by_audio[pg.get_attribute(".prompt .listen", "data-lt-say")]["ch"]
            elif t == "read":
                big = pg.inner_text(".lt-big").strip()
                want = next(c["roma"] for c in cells if c["ch"] == big)
            else:
                big = pg.inner_text(".lt-big").strip()
                want = next(c["ch"] for c in cells if c.get("hira") == big)
            check(want in opts, f"練習題的選項裡沒有正確答案（{t}：{want} / {opts}）")
            pg.click(f"[data-lt-pick='{opts.index(want) if want in opts else 0}']")
            pg.wait_for_timeout(900)
        score = pg.inner_text(".terminal .score").replace("\n", "")
        rec_ = pg.evaluate(f"JSON.parse(localStorage.getItem('{STORE_KEY}')).letters['{first['id']}']")
        check(rec_ and rec_.get("done") and rec_["best"] == rec_["total"], f"練習全對卻沒記成學完：{score} {rec_}")
        pg.goto(BASE + "#/")
        pg.wait_for_selector(".extras .extra")
        check("學完 1" in pg.inner_text(".extras"), "首頁入口格沒有顯示學完的課數")

        # 文法專欄（2026-10-03）：音檔齊全、課程表、每一課都能開、練習照答案點會記成「學完」、答錯會出現解釋
        gram = json.load(open(os.path.join(ROOT, "data", "grammar.json"), encoding="utf-8"))
        g_all = [l for g in gram["groups"] for l in g["lessons"]]
        gkeys = {e["a"] for l in g_all for e in l["ex"]} | {q["au"] for l in g_all for q in l["quiz"]}
        miss = [k for k in gkeys if not os.path.exists(os.path.join(ROOT, "audio", k + ".mp3"))]
        check(not miss, f"文法音檔缺 {len(miss)} 個：{miss[:5]}")
        pg.goto(BASE + "#/grammar")
        pg.wait_for_selector(".lt-row")
        check(pg.eval_on_selector_all(".lt-row", "els => els.length") == len(g_all), "文法課程表的課數不對")
        for l in g_all:
            pg.goto(BASE + f"#/grammar/{l['id']}")
            pg.wait_for_selector(".gm-ex")
            check(pg.eval_on_selector_all(".gm-ex", "els => els.length") == len(l["ex"]), f"{l['id']} 例句數不對")
            check(pg.eval_on_selector_all(".gm-ko em", "els => els.length") >= len(l["ex"]), f"{l['id']} 例句沒有標出重點")
            check(bool(pg.query_selector(".gm-table")) == bool(l["table"]), f"{l['id']} 表格有無不對")
        for lid in ("is", "seyo", "native"):
            L_ = next(l for l in g_all if l["id"] == lid)
            pg.goto(BASE + f"#/grammar/{lid}/practice")
            wrong_first = lid == "seyo"
            for n_ in range(40):
                pg.wait_for_selector("[data-gm-pick]:not([disabled]), .terminal")
                if pg.query_selector(".terminal"):
                    break
                t = pg.get_attribute(".stage", "data-gm-type")
                opts = pg.eval_on_selector_all(".tiles .tile", "els => els.map(e => e.innerText.trim())")
                if t == "listen":
                    key = pg.get_attribute(".listen", "data-gm-say")
                    want = next(e["zh"] for e in L_["ex"] if e["a"] == key)
                else:
                    zh = pg.inner_text(".gm-qzh").strip()
                    q = next((q for q in L_["quiz"] if q["zh"] == zh and sorted(q["o"]) == sorted(opts)), None)
                    check(q is not None, f"{lid} 找不到對應的題目：{zh} / {opts}")
                    want = q["o"][q["a"]] if q else opts[0]
                check(want in opts, f"{lid} 練習題的選項裡沒有正確答案（{t}：{want} / {opts}）")
                k_ = opts.index(want) if want in opts else 0
                if wrong_first and n_ == 0:       # 第一題故意答錯：要出現解釋與「下一題」
                    pg.click(f"[data-gm-pick='{(k_ + 1) % len(opts)}']")
                    pg.wait_for_selector(".sheet.ng")
                    if t != "listen":
                        check(bool(pg.inner_text(".gm-why").strip()), f"{lid} 答錯沒有解釋")
                    pg.click("[data-gm-next]")
                    continue
                pg.click(f"[data-gm-pick='{k_}']")
                pg.wait_for_timeout(1500 if t != "listen" else 900)
            rec_ = pg.evaluate(f"JSON.parse(localStorage.getItem('{STORE_KEY}')).grammar['{lid}']")
            if wrong_first:
                check(rec_ and rec_["best"] == rec_["total"] - 1 and rec_["done"], f"{lid} 錯一題應該還算學完：{rec_}")
            else:
                check(rec_ and rec_.get("done") and rec_["best"] == rec_["total"], f"{lid} 練習全對卻沒記成學完：{rec_}")
        pg.goto(BASE + "#/")
        pg.wait_for_selector(".extras .extra")
        check("學完 3／27" in pg.inner_text(".extras"), "首頁入口格沒有顯示文法學完的課數")

        # 數字與量詞專欄＋數字聽力（日文版，2026-10-02）：音檔齊全、變音有標色、照答案按數字鍵會全對
        npath = os.path.join(ROOT, "data", "numbers.json")
        if os.path.exists(npath):
            nums = json.load(open(npath, encoding="utf-8"))
            keys = [it["a"] for s_ in nums["sections"] for g in (s_.get("groups") or s_.get("counters")) for it in g["items"]] + [q["a"] for q in nums["quiz"]]
            miss = [k for k in keys if not os.path.exists(os.path.join(ROOT, "audio", k + ".mp3"))]
            check(not miss, f"數字音檔缺 {len(miss)} 個：{miss[:5]}")
            pg.goto(BASE + "#/numbers")
            pg.wait_for_selector(".nm-cell")
            pg.click("[data-nm-tab='1']")
            pg.wait_for_selector(".nm-ctr")
            check(pg.eval_on_selector_all(".nm-cell .r em", "els => els.length") >= 60, "量詞表沒有標出變音")
            ans_of = {q["a"]: q for q in nums["quiz"]}
            pg.goto(BASE + "#/numquiz")
            pg.click("[data-nq-count='10']")
            pg.click("[data-nq-start]")
            fields = {"price": ["n"], "date": ["m", "d"], "time": ["h", "mi"], "count": ["n"]}
            kinds_seen = set()
            for _ in range(10):
                pg.wait_for_selector(".stage[data-nq-kind] .listen")
                q = ans_of[pg.get_attribute(".prompt .listen", "data-nm-say")]
                kinds_seen.add(q["k"])
                for fi, k in enumerate(fields[q["k"]]):
                    pg.click(f"[data-nq-field='{fi}']")
                    for ch in str(q["ans"][k]):
                        pg.click(f"[data-nq-key='{ch}']")
                pg.click("[data-nq-ok]")
                pg.wait_for_selector(".sheet")
                check("ok" in (pg.get_attribute(".sheet", "class") or ""), f"照答案填卻判錯：{q['show']} {q['ans']}")
                pg.click("[data-nq-next]")
            pg.wait_for_selector(".terminal .score")
            check(pg.inner_text(".terminal .score").replace("\n", "").startswith("10"), "數字聽力全對但分數不是 10")
            check(len(kinds_seen) == 4, f"數字聽力題型不齊：{kinds_seen}")

        check(not errs, f"頁面錯誤：{errs[:3]}")
        ctx.close()

        # 離線：Service Worker 預先快取
        ctx2 = b.new_context(viewport={"width": 375, "height": 740})
        pg2 = ctx2.new_page()
        pg2.goto(BASE)
        pg2.wait_for_selector(".next")
        count_js = "caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('yeohaengmal-v')).map(k => caches.open(k).then(c => c.keys().then(r => r.length))))).then(a => a.reduce((x, y) => x + y, 0))"
        n_cached = 0
        for _ in range(20):  # 等 SW 安裝完成、預先快取寫入
            pg2.wait_for_timeout(500)
            n_cached = pg2.evaluate(count_js)
            if n_cached >= 10:
                break
        check(n_cached >= 10, f"離線快取只有 {n_cached} 個檔案")
        ctx2.close()
        b.close()

    print("通過" if not fails else f"失敗 {len(fails)} 項")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
