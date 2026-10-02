"""App 圖示（2026-10-02 改版）：背景直接用 App 的天空著色器（js/sky.js 的 FRAG＋PALETTES.day）算一張 1024px 的圖，
中央一個字（韓文版「여」＝「旅」的韓文音讀，여행＝旅行；Noto Serif KR 900，字型用 App 自己打包的 fonts/ko-serif-900.woff2）。
使用者要求（旅ことば與여행말 同一次）：圖示顏色同天空的漸層（韓文版＝ShaderGradient Halo）、取消原本的鐵軌、只留一個字。
iOS 會自己切圓角，所以輸出滿版方形；maskable 版把字縮進安全區（背景照樣滿版）。

用法（要 Playwright）：~/.claude/tools/playwright-venv/bin/python tools/make_icons.py [--variant ink|white|tile] [--t 秒數] [--out 目錄]
在瀏覽器裡用 WebGL 畫背景、用 canvas 寫字，再把 PNG 傳回來存檔。"""
import base64, functools, http.server, os, sys, threading
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = {
    "glyph": "여",
    "font": "fonts/ko-serif-900.woff2",
    "ink": "#2a1a2e",
    "t": 140.0,         # 天空著色器的時間：挑一個色團分布好看的時刻（2026-10-02 比過 61／140／230／330）
    "size": 0.6,        # 字的大小（相對於圖示邊長）
    "dy": 0.0,          # 字的垂直微調（相對於邊長）
}

PAGE = """<!doctype html><meta charset="utf-8"><body style="margin:0;background:#000">
<canvas id="gl" width="1024" height="1024"></canvas>
<script type="module">
import { FRAG, PALETTES } from './js/sky.js';
const cfg = JSON.parse(decodeURIComponent(location.hash.slice(1)));
const S = 1024;
const glc = document.getElementById('gl');
const gl = glc.getContext('webgl', { preserveDrawingBuffer: true });
const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return s; };
const prog = gl.createProgram();
gl.attachShader(prog, sh(gl.VERTEX_SHADER, 'attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}'));
gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FRAG));
gl.linkProgram(prog); gl.useProgram(prog);
gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
const loc = gl.getAttribLocation(prog, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
const U = (n) => gl.getUniformLocation(prog, n);
const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
const pal = PALETTES.day;
const cols = Array.isArray(pal) ? pal : pal.c;
gl.uniform2f(U('u_res'), S, S);
gl.uniform1f(U('u_t'), cfg.t);
gl.uniform3fv(U('u_c'), new Float32Array(cols.map(hex).flat()));
if (!Array.isArray(pal)) gl.uniform1f(U('u_b'), pal.b);
gl.uniform1f(U('u_sun'), 0); gl.uniform1f(U('u_sunY'), -1);
gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

const face = new FontFace('IconFont', `url(${cfg.font})`);
await face.load(); document.fonts.add(face); await document.fonts.ready;
window.__fontStatus = face.status;

function icon(size, scale) {
  const c = document.createElement('canvas'); c.width = c.height = S;
  const x = c.getContext('2d');
  x.filter = 'blur(10px)';   // 圖示比手機畫面的半解析度天空大很多：柔化掉顆粒與細碎紋理
  x.drawImage(glc, -40, -40, S + 80, S + 80);
  x.filter = 'none';
  const fs = S * cfg.size * scale;
  x.font = `900 ${fs}px IconFont`;
  x.textAlign = 'center'; x.textBaseline = 'alphabetic';
  // 以實際筆畫範圍置中（上下、左右留白相等）
  const m = x.measureText(cfg.glyph);
  const h = m.actualBoundingBoxAscent + m.actualBoundingBoxDescent;
  const w = m.actualBoundingBoxLeft + m.actualBoundingBoxRight;
  const bx = S / 2 - w / 2 + m.actualBoundingBoxLeft;
  const by = S / 2 + h / 2 - m.actualBoundingBoxDescent + S * cfg.dy;
  if (cfg.variant === 'tile') {
    const d = S * 0.66 * scale, r = d * 0.3, x0 = (S - d) / 2, y0 = (S - d) / 2;
    x.save();
    x.shadowColor = 'rgba(0,0,0,0.22)'; x.shadowBlur = 60; x.shadowOffsetY = 24;
    x.beginPath(); x.roundRect(x0, y0, d, d, r); x.fillStyle = 'rgba(255,255,255,0.2)'; x.fill();
    x.restore();
    x.save(); x.beginPath(); x.roundRect(x0, y0, d, d, r); x.lineWidth = 5; x.strokeStyle = 'rgba(255,255,255,0.55)'; x.stroke(); x.restore();
    x.fillStyle = cfg.ink;
  } else if (cfg.variant === 'white') {
    x.shadowColor = 'rgba(20,10,40,0.28)'; x.shadowBlur = 40; x.shadowOffsetY = 14;
    x.fillStyle = '#ffffff';
  } else {
    x.shadowColor = 'rgba(255,255,255,0.45)'; x.shadowBlur = 30; x.shadowOffsetY = 6;
    x.fillStyle = cfg.ink;
  }
  x.fillText(cfg.glyph, bx, by);
  const o = document.createElement('canvas'); o.width = o.height = size;
  const ox = o.getContext('2d'); ox.imageSmoothingQuality = 'high';
  ox.drawImage(c, 0, 0, size, size);
  return o.toDataURL('image/png');
}
window.__icons = {
  'icon-192.png': icon(192, 1), 'icon-512.png': icon(512, 1), 'apple-touch-icon.png': icon(180, 1),
  'icon-maskable-512.png': icon(512, 0.78), 'preview-1024.png': icon(1024, 1),
};
</script>"""


def main():
    args = sys.argv[1:]
    cfg = dict(CONFIG, variant="ink")
    out = os.path.join(ROOT, "icons")
    for i, a in enumerate(args):
        if a == "--variant": cfg["variant"] = args[i + 1]
        if a == "--t": cfg["t"] = float(args[i + 1])
        if a == "--out": out = args[i + 1]
    page = os.path.join(ROOT, "_icon.html")
    open(page, "w", encoding="utf-8").write(PAGE)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    handler.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        import json, urllib.parse
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
            pg = b.new_page()
            pg.goto(f"http://127.0.0.1:{srv.server_port}/_icon.html#" + urllib.parse.quote(json.dumps(cfg)))
            pg.wait_for_function("window.__icons", timeout=20000)
            icons = pg.evaluate("window.__icons")
            print('font', pg.evaluate('window.__fontStatus'))
            b.close()
        os.makedirs(out, exist_ok=True)
        for name, data in icons.items():
            if name.startswith("preview") and out == os.path.join(ROOT, "icons"):
                continue   # 預覽圖不進 repo
            open(os.path.join(out, name), "wb").write(base64.b64decode(data.split(",", 1)[1]))
        print("icons written →", out)
    finally:
        srv.shutdown()
        os.remove(page)


if __name__ == "__main__":
    main()
