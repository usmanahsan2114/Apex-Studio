# -*- coding: utf-8 -*-
"""
fast_render.py — drop-in FAST video renderer for Apex Studio.

Why: build_today_video.py cold-launches a new headless Chrome for EVERY frame
(`chrome --screenshot`). On machines where Chrome cold-start is slow (~10-12s
here), ~1900 frames => many hours. This script launches Chrome ONCE and drives
the page's deterministic `render(t)` over the DevTools Protocol (load once ->
render(t) -> captureScreenshot), turning ~12s/frame into ~0.1-0.3s/frame.

It REUSES build_today_video's own HTML/audio/encode so output is identical:
  python fast_render.py            # full render -> generated_images/video/ (uses APEX_SPEC)
  python fast_render.py test       # quick: 8 instagram frames to scratchpad, no audio
"""
import base64, hashlib, json, os, shutil, socket, subprocess, sys, time, urllib.request, tempfile
from io import BytesIO
import numpy as np
import websocket
from PIL import Image
import build_today_video as V
import build_today_pack as pack

CHROME = V.CHROME
PROFILE = os.path.join(tempfile.gettempdir(), "apex_chrome_fast_prof")
FAST_FLAGS = [
    "--headless", "--disable-gpu", "--hide-scrollbars",
    "--no-first-run", "--no-default-browser-check", "--disable-extensions",
    "--disable-background-networking", "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows", "--disable-renderer-backgrounding",
    "--disable-component-update", "--disable-default-apps", "--disable-sync",
    "--metrics-recording-only", "--mute-audio", "--no-pings",
    "--disable-features=Translate,BackForwardCache,AcceptCHFrame,MediaRouter,OptimizationHints",
    "--safebrowsing-disable-auto-update", "--disable-domain-reliability",
]
# Lush mode needs software WebGL (three.js), so NOT --disable-gpu; force ANGLE+SwiftShader.
WEBGL_FLAGS = [
    "--headless=new", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
    "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--enable-webgl",
    "--use-gl=angle", "--use-angle=swiftshader", "--mute-audio",
    "--disable-background-networking", "--disable-component-update", "--no-pings",
]
LUSH = bool(os.environ.get("APEX_LUSH"))
# ---- cinema-grade fidelity knobs (env-tunable; Max defaults). Render time scales ~ SCALE^2 * BLUR * (FPS/30).
# SCALE 2 = supersampled (4x pixels -> crisp type); BLUR = motion-blur sub-samples averaged per frame.
# Dial down for quick drafts: APEX_SCALE=1 APEX_BLUR=1 ; push hero posts: APEX_SCALE=3 APEX_BLUR=4 APEX_FPS=60.
SCALE = max(1, int(os.environ.get("APEX_SCALE", "1" if LUSH else "2")))  # 1 = native 1:1 (crisp + fast); env 2/3 = supersample hero (much slower on software render)
BLUR = max(1, int(os.environ.get("APEX_BLUR", "3")))      # sub-frames averaged -> cinematic motion blur (the affordable Max win; 1 = off)
CRF = os.environ.get("APEX_CRF", "16")                    # H.264 quality (lower=better)
PRESET = os.environ.get("APEX_PRESET", "veryslow")        # final encode effort (one pass/aspect)
CAPQ = int(os.environ.get("APEX_CAPQ", "95"))             # JPEG capture quality (near-lossless, ~2x faster than PNG)
FRAME_EXT = "jpg"

def _build_html(aspect, concept, tl):
    """Lush v4 (WebGL/three.js) when APEX_LUSH, else the standard build_today_video page."""
    if LUSH:
        import apex_lush
        return apex_lush.build_lush_html(aspect, concept, tl)
    return V.build_anim_html(aspect, concept, tl)

def _free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p

class Chrome:
    def __init__(self):
        self.port = _free_port()
        # Unique profile per run: a fixed dir lets a zombie Chrome (e.g. from an interrupted
        # render) hold its SingletonLock and refuse every later launch (WinError 10061).
        self.profile = f"{PROFILE}_{os.getpid()}_{self.port}"
        shutil.rmtree(self.profile, ignore_errors=True)
        args = [CHROME, f"--remote-debugging-port={self.port}", "--remote-allow-origins=*",
                f"--user-data-dir={self.profile}"] + (WEBGL_FLAGS if LUSH else FAST_FLAGS) + ["about:blank"]
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._wait_ready()
        page = self._http("PUT", "/json/new?about:blank")
        self.ws = websocket.create_connection(page["webSocketDebuggerUrl"], max_size=None, timeout=120)
        self._id = 0
        self.cmd("Page.enable"); self.cmd("Runtime.enable")

    def _http(self, method, path, tries=60):
        last = None
        for _ in range(tries):
            try:
                req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", method=method)
                return json.loads(urllib.request.urlopen(req, timeout=5).read())
            except Exception as ex:
                last = ex; time.sleep(0.5)
        raise RuntimeError(f"chrome devtools {method} {path} failed: {last}")

    def _wait_ready(self):
        self._http("GET", "/json/version")

    def cmd(self, method, params=None, timeout=120):
        self._id += 1; mid = self._id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg: raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
        raise TimeoutError(method)

    def wait_load(self, timeout=60):
        end = time.time() + timeout
        while time.time() < end:
            msg = json.loads(self.ws.recv())
            if msg.get("method") == "Page.loadEventFired":
                return
        raise TimeoutError("load")

    def close(self):
        try: self.ws.close()
        except Exception: pass
        try: self.proc.terminate(); self.proc.wait(timeout=10)
        except Exception:
            try: self.proc.kill()
            except Exception: pass
        try: shutil.rmtree(self.profile, ignore_errors=True)
        except Exception: pass

def encode_jpg(aspect, fdir, audio):
    """Encode the PNG frame intermediates + audio to the final H.264 MP4 (lossless input,
    CRF/preset env-tunable). Frames are already at output size (downsampled in render_aspect)."""
    A = V.ASPECTS[aspect]; out = os.path.join(V.VIDEO_DIR, A["out"])
    subprocess.run([V.FF, "-y", "-framerate", str(V.FPS), "-i", os.path.join(fdir, f"frame_%05d.{FRAME_EXT}"),
        "-i", audio, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", str(CRF), "-preset", PRESET, "-vf", f"scale={A['w']}:{A['h']}:flags=lanczos,format=yuv420p",
        "-r", str(V.FPS), "-c:a", "aac", "-b:a", "192k", "-ar", str(V.SR),
        "-movflags", "+faststart", "-shortest", out], check=True, capture_output=True)
    return out

def render_aspect(ch, aspect, concept, tl, fdir):
    A = V.ASPECTS[aspect]; W, H = A["w"], A["h"]
    os.makedirs(fdir, exist_ok=True)
    html = os.path.join(V.TMP, f"fast_{aspect}.html")
    with open(html, "w", encoding="utf-8") as f:
        f.write(_build_html(aspect, concept, tl))
    ch.cmd("Emulation.setDeviceMetricsOverride",
           {"width": W, "height": H, "deviceScaleFactor": SCALE, "mobile": False})
    ch.cmd("Page.navigate", {"url": "file:///" + html.replace("\\", "/")})
    ch.wait_load()
    n = int(round(tl["total"] * V.FPS))
    t0 = time.time()

    def grab(t):  # render(t) -> downsampled RGB frame (supersample crisping happens here)
        ch.cmd("Runtime.evaluate", {"expression": f"render({t});", "returnByValue": True})
        shot = ch.cmd("Page.captureScreenshot", {"format": "jpeg", "quality": CAPQ, "captureBeyondViewport": False})
        im = Image.open(BytesIO(base64.b64decode(shot["data"]))).convert("RGB")
        if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
        return im

    for f in range(n):
        if BLUR <= 1:
            img = grab(f / V.FPS)
        else:  # motion blur: average BLUR deterministic sub-samples across the frame interval
            acc = None
            for s in range(BLUR):
                a = np.asarray(grab((f + s / BLUR) / V.FPS), dtype=np.float32)
                acc = a if acc is None else acc + a
            img = Image.fromarray(np.clip(acc / BLUR + 0.5, 0, 255).astype(np.uint8))
        img.save(os.path.join(fdir, f"frame_{f:05d}.{FRAME_EXT}"), quality=95)
        if f % 30 == 0 or f == n - 1:
            el = time.time() - t0; r = (f + 1) / max(el, 1e-6)
            print(f"  [{aspect}] {f+1}/{n}  {r:.2f} fps  eta {((n-f-1)/max(r,1e-6)):.0f}s", flush=True)
    return n

def test():
    os.environ.setdefault("APEX_SPEC", os.path.join(V.ROOT, "day_spec.json"))
    concept = V.get_concept()
    tl = V.build_timeline([4.0, 4.5, 3.0, 4.0, 4.5, 3.5], concept.get("look"))
    print("TEST concept=%s look=%s/%s total=%.2fs" %
          (concept["id"], concept["look"]["lookbook"], concept["look"]["theme"], tl["total"]))
    os.makedirs(V.TMP, exist_ok=True)
    fdir = os.path.join(V.TMP, "fast_test")
    if os.path.isdir(fdir): shutil.rmtree(fdir)
    os.makedirs(fdir)
    A = V.ASPECTS["instagram"]; W, H = A["w"], A["h"]
    html = os.path.join(V.TMP, "fast_test.html")
    with open(html, "w", encoding="utf-8") as f:
        f.write(_build_html("instagram", concept, tl))
    ch = Chrome()
    try:
        ch.cmd("Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": SCALE, "mobile": False})
        ch.cmd("Page.navigate", {"url": "file:///" + html.replace("\\", "/")}); ch.wait_load()
        N = 10; t0 = time.time()
        for i in range(N):
            t = (i / (N - 1)) * tl["total"]
            ch.cmd("Runtime.evaluate", {"expression": f"render({t});", "returnByValue": True})
            shot = ch.cmd("Page.captureScreenshot", {"format": "jpeg", "quality": 92})
            img = Image.open(BytesIO(base64.b64decode(shot["data"]))).convert("RGB")
            if img.size != (W, H): img = img.resize((W, H), Image.LANCZOS)
            out = os.path.join(fdir, f"t{i}.jpg"); img.save(out, "JPEG", quality=95)
            print(f"  frame {i+1}/{N} t={t:.2f}s size={img.size} {os.path.getsize(out)//1024}KB", flush=True)
        dt = time.time() - t0
        print("TEST OK: %d frames in %.2fs (%.1f fps) -> %s" % (N, dt, N/dt, fdir))
    finally:
        ch.close()

def test3d():
    os.makedirs(V.TMP, exist_ok=True)
    html = os.path.join(V.TMP, "apex_test3d.html")
    src = """<!doctype html><html><head><meta charset='utf-8'><style>
@page{margin:0}html,body{width:640px;height:640px;margin:0;background:#0F1115;overflow:hidden}
.scene{position:relative;width:640px;height:640px;perspective:900px;background:radial-gradient(circle at 50% 40%,rgba(255,190,11,.12),transparent 55%),#0F1115}
.card{position:absolute;left:220px;top:220px;width:200px;height:130px;transform-style:preserve-3d;will-change:transform}
.face{position:absolute;inset:0;border:1px solid rgba(255,190,11,.4);background:linear-gradient(135deg,rgba(255,190,11,.4),rgba(255,255,255,.08));box-shadow:0 30px 80px rgba(0,0,0,.35)}
.f0{transform:translateZ(36px)}.f1{transform:rotateY(90deg) translateZ(100px);width:72px;left:64px}.f2{transform:rotateX(90deg) translateZ(65px);height:72px;top:29px}
</style></head><body><div class='scene'><div id='card' class='card'><div class='face f0'></div><div class='face f1'></div><div class='face f2'></div></div></div>
<script>function render(t){document.getElementById('card').style.transform='rotateX('+(-12+Math.sin(t)*8)+'deg) rotateY('+(t*46)+'deg) translateZ(20px)'}</script></body></html>"""
    with open(html, "w", encoding="utf-8") as f:
        f.write(src)
    ch = Chrome()
    try:
        ch.cmd("Emulation.setDeviceMetricsOverride", {"width": 640, "height": 640, "deviceScaleFactor": 1, "mobile": False})
        ch.cmd("Page.navigate", {"url": "file:///" + html.replace("\\", "/")}); ch.wait_load()
        hashes = []
        for t in (0.0, 1.0, 1.0):
            ch.cmd("Runtime.evaluate", {"expression": f"render({t});", "returnByValue": True})
            shot = ch.cmd("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
            data = base64.b64decode(shot["data"])
            hashes.append(hashlib.sha256(data).hexdigest())
        changed = hashes[0] != hashes[1]
        deterministic = hashes[1] == hashes[2]
        print("TEST3D changed_across_time=%s deterministic_same_time=%s" % (changed, deterministic))
        if not (changed and deterministic):
            raise SystemExit(1)
    finally:
        ch.close()

def main():
    os.environ.setdefault("APEX_SPEC", os.path.join(V.ROOT, "day_spec.json"))
    concept = V.get_concept()
    tl, audio = V.build_audio(concept)
    print("concept=%s look=%s/%s total=%.2fs" %
          (concept["id"], concept["look"]["lookbook"], concept["look"]["theme"], tl["total"]), flush=True)
    os.makedirs(V.VIDEO_DIR, exist_ok=True)
    ch = Chrome()
    try:
        for aspect in ("instagram", "linkedin"):
            fdir = os.path.join(V.TMP, f"frames_{aspect}")
            if os.path.isdir(fdir): shutil.rmtree(fdir)
            render_aspect(ch, aspect, concept, tl, fdir)
            out = encode_jpg(aspect, fdir, audio); info = V.probe(out)
            import re
            v = re.search(r"Video: (\w+).*?(\d{3,4}x\d{3,4}).*?([\d.]+) fps", info, re.S)
            a = re.search(r"Audio: (\w+).*?(\d+) Hz", info, re.S)
            print(f"  {aspect}: {os.path.getsize(out)//1024}KB | "
                  f"{v.group(1) if v else '?'} {v.group(2) if v else '?'} {v.group(3) if v else '?'}fps | "
                  f"{a.group(1) if a else '?'} {a.group(2) if a else '?'}Hz", flush=True)
            shutil.rmtree(fdir)
    finally:
        ch.close()
    V.write_captions(concept)  # video.md + linkedin.md + fb.md, all in sync with this concept
    print("DONE. video/ holds:", sorted(os.listdir(V.VIDEO_DIR)), flush=True)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test()
    elif len(sys.argv) > 1 and sys.argv[1] == "test3d":
        test3d()
    else:
        main()
