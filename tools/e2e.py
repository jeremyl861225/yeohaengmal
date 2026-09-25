"""端對端驗收（手機視窗）：用 Playwright 實際操作 App。

用法：~/.claude/tools/playwright-venv/bin/python tools/e2e.py [http://127.0.0.1:8731/] [--all-cards]
先在 repo 根目錄開本機伺服器：python3 -m http.server 8731 --bind 127.0.0.1
"""
import json, os, sys, time
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = next((a for a in sys.argv[1:] if a.startswith("http")), "http://127.0.0.1:8731/")
ALL = "--all-cards" in sys.argv
data = json.load(open(os.path.join(ROOT, "data", "cards.json"), encoding="utf-8"))
cards = data["cards"]
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("  ✗", msg)


def main():
    # 音檔齊全（檔案系統）
    missing = [f"{v}/{c['id']}{s}" for c in cards for v in ("n", "k") for s in ("", "x")
               if (s == "" or c.get("ex")) and not os.path.exists(os.path.join(ROOT, "audio", v, f"{c['id']}{s}.mp3"))]
    check(not missing, f"缺音檔 {len(missing)} 個：{missing[:6]}")

    with sync_playwright() as p:
        b = p.chromium.launch()
        # 開場動畫：會自己消失、點一下可以跳過（主要測試用減少動態效果，開場不顯示、不擋點擊）
        sctx = b.new_context(viewport={"width": 375, "height": 740}, is_mobile=True, has_touch=True, service_workers="block")
        sp = sctx.new_page()
        sp.goto(BASE, wait_until="commit")
        sp.wait_for_selector("#splash .sun", state="attached")
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

        # 每張卡：沒有橫向溢出、假名數量正確
        sample = cards if ALL else cards[:: max(1, len(cards) // 120)]
        t0 = time.time()
        for c in sample:
            pg.evaluate(f"location.hash = '#/card/{c['id']}'")
            pg.wait_for_selector(".card .word")
            over = pg.evaluate("document.scrollingElement.scrollWidth - window.innerWidth")
            check(over <= 1, f"{c['id']} {c['w']} 橫向溢出 {over}px")
            n_rt = pg.eval_on_selector_all(".card .word rt", "els => els.length")
            check(n_rt == c["w"].count("{"), f"{c['id']} 單字假名數 {n_rt} ≠ {c['w'].count('{')}")
            if c.get("ex"):
                n_rt2 = pg.eval_on_selector_all(".ex-ja rt", "els => els.length")
                check(n_rt2 == c["ex"].count("{"), f"{c['id']} 例句假名數 {n_rt2} ≠ {c['ex'].count('{')}")
            wh = pg.eval_on_selector(".card .word", "e => e.getBoundingClientRect().height")
            fs = pg.eval_on_selector(".card .word", "e => parseFloat(getComputedStyle(e).fontSize)")
            check(wh < fs * 1.35 * 3.2, f"{c['id']} {c['w']} 單字換太多行（高 {wh:.0f}px）")
        print(f"字卡檢查 {len(sample)} 張，{time.time() - t0:.1f}s")

        # 搜尋：漢字、假名、羅馬拼音、中文
        target = next((c for c in cards if "{" in c["w"] and c.get("rm")), cards[0])
        pg.goto(BASE + "#/browse")
        pg.wait_for_selector("#q")
        head = "".join(ch for ch in target["w"] if ch not in "{}|")
        for q in (target["r"], target["rm"], target["zh"].split("；")[0].split("、")[0]):
            pg.fill("#q", q)
            pg.wait_for_timeout(150)
            ids = pg.eval_on_selector_all(".row", "els => els.map(e => e.getAttribute('href'))")
            check(f"#/card/{target['id']}" in ids, f"搜尋「{q}」找不到 {target['id']}")

        # 篩選標籤列：捲到右邊再點，列表不能跳回最前面
        pg.evaluate("document.querySelectorAll('.chips')[1].scrollLeft = 400")
        x0 = pg.evaluate("document.querySelectorAll('.chips')[1].scrollLeft")
        pg.evaluate("""(() => { const row = document.querySelectorAll('.chips')[1]; const box = row.getBoundingClientRect();
            [...row.querySelectorAll('[data-f-th]')].find((b) => { const r = b.getBoundingClientRect(); return r.left > box.left + 4 && r.right < box.right - 4; }).click(); })()""")
        pg.wait_for_timeout(200)
        x1 = pg.evaluate("document.querySelectorAll('.chips')[1].scrollLeft")
        check(x0 > 0 and abs(x1 - x0) < 40, f"點主題標籤後標籤列跳動：{x0} → {x1}")
        pg.click("[data-f-th='']")

        # 測驗：第一課全部作答到終點
        u = data["units"][0]
        pg.goto(BASE + f"#/unit/{u['id']}")
        pg.click("[data-unit-quiz]")
        kinds = set()
        for i in range(len(u["cards"])):
            pg.wait_for_selector("[data-choice], [data-tile]")
            kinds.add(pg.inner_text(".q-kind"))
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

        # 星號與不熟清單
        pg.goto(BASE + f"#/card/{cards[1]['id']}")
        pg.wait_for_selector(".topbar .star-btn")
        pg.click(".topbar .star-btn")
        pg.goto(BASE + "#/starred")
        pg.wait_for_selector(".row, .empty")
        check(pg.eval_on_selector_all(".row", "els => els.length") >= 1, "加星後不熟清單是空的")
        badge = pg.inner_text(".tab[data-tab='starred'] .badge-n")
        check(badge.strip() != "" and badge.strip() != "0", "分頁上的不熟數字沒更新")

        # 設定：隱藏假名
        pg.goto(BASE + "#/settings")
        pg.click("[data-set='furigana'][data-val='none']")
        pg.goto(BASE + f"#/card/{target['id']}")
        pg.wait_for_selector(".card .word rt", state="attached")
        vis = pg.eval_on_selector(".card .word rt", "e => getComputedStyle(e).visibility")
        check(vis == "hidden", "設定隱藏假名後仍看得到假名")
        check(not errs, f"頁面錯誤：{errs[:3]}")
        ctx.close()

        # 離線：Service Worker 預先快取
        ctx2 = b.new_context(viewport={"width": 375, "height": 740})
        pg2 = ctx2.new_page()
        pg2.goto(BASE)
        pg2.wait_for_selector(".next")
        count_js = "caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('tabi-kotoba-v')).map(k => caches.open(k).then(c => c.keys().then(r => r.length))))).then(a => a.reduce((x, y) => x + y, 0))"
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
