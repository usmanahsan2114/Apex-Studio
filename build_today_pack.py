# -*- coding: utf-8 -*-
"""
Apex IT Solutions x Apex Marketings daily post -> 5-slide CAROUSEL, two themes.
Centered / symmetric layout, richly textured background (grain + dot-grid +
ambient glow + concentric signal rings + corner brackets + carousel dots).

Monochrome + single amber accent:
  Apex IT    = ink #171717  (off-white on dark)  -> neutral / BUILD
  Apex Mktgs = amber #FFBE0B (bronze on light)    -> accent / GROWTH

Output in generated_images/:
  linkedin-dark/ 01..05.png   linkedin-light/ 01..05.png
  fb-dark/       01..05.png   fb-light/       01..05.png
  linkedin.md    fb.md
"""
import base64, os, re, shutil, subprocess, tempfile
from PIL import Image

ROOT   = os.path.dirname(os.path.abspath(__file__))   # portable: the repo folder
LOGO   = os.path.join(ROOT, "logos")
VAR    = os.path.join(LOGO, "variants")
OUT    = os.path.join(ROOT, "generated_images")
CHROME = next((p for p in [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
] if os.path.exists(p)), r"C:\Program Files\Google\Chrome\Application\chrome.exe")
W, H = 1080, 1350
KEEP_DIRS  = {"linkedin-dark", "linkedin-light", "fb-dark", "fb-light", "video"}
KEEP_FILES = {"linkedin.md", "fb.md", "video.md"}
KICKER = "Owned Demand System"   # carousel kicker (overridable via env APEX_SPEC)
LUSH = bool(os.environ.get("APEX_LUSH"))   # 1 => render the dark "lush" carousel (matches the video look)

def token_map():
    m = {}
    for f in os.listdir(VAR):
        if f.lower().endswith(".png"):
            with open(os.path.join(VAR, f), "rb") as fh:
                m["__%s__" % os.path.splitext(f)[0]] = "data:image/png;base64," + base64.b64encode(fh.read()).decode()
    return m
LOGO_TOKENS = token_map()
def inject(html):
    for tok, uri in LOGO_TOKENS.items(): html = html.replace(tok, uri)
    left = sorted(set(re.findall(r"__[A-Z0-9_]+__", html)))
    if left: print("  WARNING leftover tokens:", left)
    return html

GRAIN = "data:image/svg+xml;base64," + base64.b64encode((
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">'
    '<filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/>'
    '<feColorMatrix type="saturate" values="0"/></filter>'
    '<rect width="200" height="200" filter="url(#n)"/></svg>').encode()).decode()

def hex_rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# Single dial for the *new* subtle background-depth layers (mesh/vignette/guides/ghost).
# 1.0 = tuned subtle default. 0 = off (collapses to the clean look). ~1.3 = a touch more.
BG_INTENSITY = 1.0
def bgop(base):
    return round(min(1.0, max(0.0, base * BG_INTENSITY)), 3)

PALETTES = {
    "dark": {
        "base": "#0F1115", "bg_grad": "linear-gradient(168deg,#17181d,#141417 46%,#101218)",
        "hairline": "#33343A", "bracket": "rgba(255,255,255,.16)",
        "text_primary": "#ECEDF0", "text_secondary": "#AEB3BC", "text_tertiary": "#9398A2",
        "neutral": "#ECEDF0", "chip_b_border": "rgba(236,237,240,.34)", "chip_b_text": "#D2D5DB",
        "amber": "#FFBE0B", "chip_g_border": "rgba(255,190,11,.55)", "chip_g_text": "#FFD98A",
        "qbar": "linear-gradient(90deg,#ECEDF0,#FFBE0B)", "meter_track": "rgba(255,255,255,.10)",
        "grain": "0.06", "dot": "rgba(255,255,255,.04)",
        "glow": "radial-gradient(760px 620px at 50% 38%, rgba(255,190,11,.10), transparent 62%)",
        "ring": "rgba(255,255,255,.07)", "ring_a": "rgba(255,190,11,.20)",
        "mesh": ("radial-gradient(680px 560px at 22% 26%, rgba(120,132,150,.10), transparent 60%),"
                 "radial-gradient(720px 600px at 82% 80%, rgba(120,132,150,.07), transparent 62%)"),
        "vignette": "radial-gradient(120% 100% at 50% 44%, transparent 64%, rgba(0,0,0,.05) 100%)",
        "guide": "rgba(255,255,255,.05)", "tick": "rgba(255,255,255,.10)", "ghost": "rgba(255,255,255,.037)",
        "dot_off": "rgba(255,255,255,.22)", "lane_glow": "0 0 16px rgba(255,190,11,.5)",
        "logo_arrow": "__ARROW_OFFWHITE__", "logo_m": "__M_AMBER_BRAND__",
    },
    "light": {
        "base": "#F7F8FA", "bg_grad": "linear-gradient(168deg,#FFFFFF,#F6F7FA 46%,#EEF0F4)",
        "hairline": "#DDE0E6", "bracket": "rgba(23,23,23,.18)",
        "text_primary": "#161616", "text_secondary": "#454B55", "text_tertiary": "#5C636E",
        "neutral": "#171717", "chip_b_border": "rgba(23,23,23,.24)", "chip_b_text": "#171717",
        "amber": "#B5791A", "chip_g_border": "rgba(181,121,26,.5)", "chip_g_text": "#8A5C12",
        "qbar": "linear-gradient(90deg,#171717,#D79A12)", "meter_track": "rgba(20,22,26,.10)",
        "grain": "0.035", "dot": "rgba(23,23,23,.045)",
        "glow": "radial-gradient(760px 620px at 50% 38%, rgba(255,190,11,.10), transparent 62%)",
        "ring": "rgba(23,23,23,.07)", "ring_a": "rgba(181,121,26,.22)",
        "mesh": ("radial-gradient(680px 560px at 22% 26%, rgba(70,80,95,.045), transparent 60%),"
                 "radial-gradient(720px 600px at 82% 80%, rgba(70,80,95,.03), transparent 62%)"),
        "vignette": "radial-gradient(120% 100% at 50% 44%, transparent 66%, rgba(23,23,23,.03) 100%)",
        "guide": "rgba(23,23,23,.045)", "tick": "rgba(23,23,23,.085)", "ghost": "rgba(23,23,23,.035)",
        "dot_off": "rgba(23,23,23,.20)", "lane_glow": "none",
        "logo_arrow": "__ARROW_INK17__", "logo_m": "__M_INK17__",
    },
}

def rings_svg(P):
    c = 520
    circ = lambda r, col, w, dash: f'<circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="{col}" stroke-width="{w}" stroke-dasharray="{dash}"/>'
    return (f'<svg class="rings" width="1040" height="1040" viewBox="0 0 1040 1040">'
            + circ(150, P["ring"], 1.4, "2 9") + circ(250, P["ring"], 1.4, "2 9")
            + circ(360, P["ring_a"], 1.6, "2 10") + circ(470, P["ring"], 1.2, "2 11")
            + circ(515, P["ring"], 1.0, "0") + '</svg>')

def guides(P):
    g, tk = P["guide"], P["tick"]
    cx, ml, mr = W // 2, 78, W - 78
    mt, mb = 150, H - 130
    L = [f'<line x1="{ml}" y1="{mt}" x2="{mr}" y2="{mt}" stroke="{g}" stroke-width="1"/>',
         f'<line x1="{ml}" y1="{mb}" x2="{mr}" y2="{mb}" stroke="{g}" stroke-width="1"/>',
         f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mb}" stroke="{g}" stroke-width="1"/>',
         f'<line x1="{mr}" y1="{mt}" x2="{mr}" y2="{mb}" stroke="{g}" stroke-width="1"/>',
         f'<line x1="{cx}" y1="{mt}" x2="{cx}" y2="432" stroke="{g}" stroke-width="1"/>',
         f'<line x1="{cx}" y1="918" x2="{cx}" y2="{mb}" stroke="{g}" stroke-width="1"/>']
    for i, x in enumerate(range(135, W - 90, 90)):
        h = 11 if i % 3 == 0 else 6
        L.append(f'<line x1="{x}" y1="30" x2="{x}" y2="{30 + h}" stroke="{tk}" stroke-width="1"/>')
        L.append(f'<line x1="{x}" y1="{H - 30}" x2="{x}" y2="{H - 30 - h}" stroke="{tk}" stroke-width="1"/>')
    return f'<svg class="guides" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(L)}</svg>'

def ghost_glyph(P, idx):
    return (f'<svg class="ghost" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<text x="{W - 30}" y="{H + 78}" text-anchor="end" '
            f'font-family="Segoe UI,Arial,sans-serif" font-weight="800" font-size="540" '
            f'letter-spacing="-18" fill="{P["ghost"]}">{idx:02d}</text></svg>')

def dots_ind(P, idx, total):
    s = '<div class="dind">'
    for i in range(1, total + 1):
        s += f'<span class="pd{" on" if i == idx else ""}"></span>'
    return s + '</div>'

def doc(look, theme, idx, total, inner):
    import apex_art
    import apex_icons
    if look is None: look = apex_art.choose_look({}, kind="carousel")
    P = apex_art.palette_for(look, theme)
    layers_css = apex_art.world_css(look, theme, W, H)      # background world + accents (per look)
    layers_html = apex_art.world_html(look, theme, W, H, idx)
    font_css = apex_art.fontface_css(look)
    icon_css = apex_icons.css(P)
    layout_over = apex_art.layout_css(look, W, H, kind="carousel")
    d3_css = apex_art.d3_css(look, theme)
    d3_html = apex_art.d3_html(look, theme)
    type_over = apex_art.type_css(look)                     # headline weight/tracking/scale + align
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ margin:0; }} * {{ box-sizing:border-box; margin:0; padding:0; }}
html,body {{ width:{W}px; height:{H}px; }}
{font_css}
body {{ font-family:'Segoe UI','Inter',Arial,sans-serif; background:{P['base']}; color:{P['text_primary']}; -webkit-font-smoothing:antialiased; overflow:hidden; }}
.canvas {{ position:relative; width:{W}px; height:{H}px; background:{P['bg_grad']}; padding:70px 78px 62px; display:flex; flex-direction:column; justify-content:space-between; align-items:center; text-align:center; overflow:hidden; }}
{layers_css}
{icon_css}
{d3_css}

.head {{ position:relative; z-index:3; display:flex; flex-direction:column; align-items:center; gap:14px; }}
.kicker {{ font-size:15px; font-weight:700; letter-spacing:4px; color:{P['text_tertiary']}; text-transform:uppercase; }}
.splitbar {{ display:flex; width:120px; height:4px; border-radius:3px; overflow:hidden; }}
.splitbar .n {{ flex:1; background:{P['neutral']}; }}
.splitbar .a {{ flex:1; background:{P['amber']}; box-shadow:{P['lane_glow']}; }}

.body {{ position:relative; z-index:3; flex:1 1 auto; display:flex; flex-direction:column; justify-content:center; align-items:center; width:100%; }}

.hxl {{ font-size:84px; font-weight:800; line-height:1.0; letter-spacing:-2.2px; color:{P['text_primary']}; text-wrap:balance; }}
.hlg {{ font-size:58px; font-weight:800; line-height:1.04; letter-spacing:-1.4px; color:{P['text_primary']}; text-wrap:balance; }}
.hlg b, .hxl b {{ color:{P['amber']}; }}
.sub {{ margin:28px auto 0; font-size:28px; font-weight:400; line-height:1.5; color:{P['text_secondary']}; max-width:800px; }}
.sub b {{ color:{P['text_primary']}; font-weight:700; }}
.tag {{ font-size:15px; font-weight:800; letter-spacing:3px; text-transform:uppercase; color:{P['amber']}; margin-bottom:26px; }}
.swipe {{ margin-top:42px; font-size:17px; font-weight:800; letter-spacing:3px; text-transform:uppercase; color:{P['amber']}; }}
.stamp {{ display:inline-flex; align-items:center; gap:11px; font-size:17px; font-weight:600; letter-spacing:.3px; font-variant-numeric:tabular-nums; color:{P['text_secondary']}; margin-bottom:30px; }}
.stamp .arr {{ color:{P['amber']}; font-weight:700; }}
.stamp .sdot {{ width:8px; height:8px; border-radius:50%; background:{P['amber']}; box-shadow:{P['lane_glow']}; }}

.meter {{ margin:42px auto 0; width:560px; max-width:80%; }}
.mhead {{ font-size:14px; font-weight:700; letter-spacing:2.5px; text-transform:uppercase; color:{P['text_secondary']}; margin-bottom:14px; }}
.mtrack {{ height:7px; border-radius:4px; background:{P['meter_track']}; position:relative; }}
.mfill {{ position:absolute; left:0; top:0; bottom:0; width:84%; border-radius:4px; background:{P['qbar']}; }}
.mknob {{ position:absolute; left:84%; top:50%; width:14px; height:14px; border-radius:50%; background:{P['amber']}; transform:translate(-50%,-50%); box-shadow:{P['lane_glow']}; }}
.mends {{ display:flex; justify-content:space-between; margin-top:13px; font-size:17px; font-weight:600; font-variant-numeric:tabular-nums; color:{P['text_secondary']}; }}
.mends .goal {{ color:{P['amber']}; }}

.split {{ margin:46px auto 0; display:grid; grid-template-columns:1fr 1px 1fr; align-items:start; gap:0; width:760px; max-width:92%; }}
.divider {{ background:{P['hairline']}; align-self:stretch; }}
.col {{ padding:0 30px; display:flex; flex-direction:column; align-items:center; }}
.lab {{ font-size:25px; font-weight:800; letter-spacing:1px; color:{P['text_primary']}; text-transform:uppercase; }}
.lab .dot {{ display:inline-block; width:11px; height:11px; border-radius:3px; vertical-align:middle; margin-right:9px; }}
.lab .dn {{ background:{P['neutral']}; }} .lab .da {{ background:{P['amber']}; }}
.brand {{ font-size:16px; font-weight:600; letter-spacing:.4px; color:{P['text_secondary']}; margin-top:8px; }}
.chips {{ margin-top:20px; display:flex; gap:10px; flex-wrap:wrap; justify-content:center; }}
.chip {{ font-size:15px; font-weight:700; letter-spacing:1px; text-transform:uppercase; padding:12px 18px; border-radius:5px; border:1px solid {P['hairline']}; }}
.chip.n {{ border-color:{P['chip_b_border']}; color:{P['chip_b_text']}; }}
.chip.a {{ border-color:{P['chip_g_border']}; color:{P['chip_g_text']}; }}
.ctabox {{ margin:34px auto 0; font-size:28px; font-weight:600; line-height:1.45; color:{P['text_secondary']}; max-width:760px; }}
.ctabox b {{ color:{P['text_primary']}; font-weight:800; }}

.foot {{ position:relative; z-index:3; display:flex; flex-direction:column; align-items:center; gap:20px; width:100%; }}
.dind {{ display:flex; gap:9px; }}
.pd {{ width:8px; height:8px; border-radius:50%; background:{P['dot_off']}; }}
.pd.on {{ width:26px; border-radius:5px; background:{P['amber']}; box-shadow:{P['lane_glow']}; }}
.lockup {{ display:flex; align-items:center; justify-content:center; gap:16px; padding-top:18px; border-top:1px solid {P['hairline']}; width:100%; }}
.bm {{ display:flex; align-items:center; gap:13px; }}
.bm img {{ display:block; }}
.bname {{ font-size:17px; font-weight:800; letter-spacing:1.3px; color:{P['text_primary']}; text-transform:uppercase; }}
.xsep {{ font-size:15px; color:{P['text_tertiary']}; font-weight:600; padding:0 4px; }}
{type_over}
{layout_over}
</style></head><body>
<div class="canvas">
  {layers_html}
  {d3_html}
  <div class="head"><div class="kicker">{KICKER}</div><div class="splitbar"><span class="n"></span><span class="a"></span></div></div>
  <div class="body">{inner}</div>
  <div class="foot">
    {dots_ind(P, idx, total)}
    <div class="lockup">
      <div class="bm"><img src="{P['logo_arrow']}" height="27" alt=""><span class="bname">Apex IT Solutions</span></div>
      <span class="xsep">&times;</span>
      <div class="bm"><span class="bname">Apex Marketings</span><img src="{P['logo_m']}" height="33" alt=""></div>
    </div>
  </div>
</div></body></html>"""

SLIDES = [
  """<div class="stamp"><span class="sdot"></span> Pause ads <span class="arr">&rarr;</span> traffic 0</div>
     <h1 class="hxl">Ads are <b>rent</b>.<br>Stop paying,<br>traffic hits zero.</h1>
     <p class="sub">Every month you don't run ads, the traffic you bought disappears. You rented it. You never owned it.</p>
     <div class="swipe">Swipe &rarr;</div>""",

  """<div class="tag">THE TRAP</div>
     <h2 class="hlg">You're scaling the rent<br>on a <b>cracked</b> foundation.</h2>
     <p class="sub">A slow, thin site leaks every click you pay for. More budget just buys more leaks, faster.</p>
     <div class="meter"><div class="mhead">WHAT YOUR SPEND BUILDS</div>
       <div class="mtrack"><div class="mfill"></div><div class="mknob"></div></div>
       <div class="mends"><span>Rented traffic</span><span class="goal">An owned asset</span></div></div>""",

  """<h2 class="hxl">Ads rent attention.<br>A site + SEO<br><b>own</b> it — and compound.</h2>
     <p class="sub">Rent resets to zero the day you stop. An asset keeps paying you long after the invoice clears.</p>""",

  """<div class="tag">THE FIX</div>
     <h2 class="hlg">Fix the <b>asset</b><br>before you scale the rent.</h2>
     <div class="split">
       <div class="col"><div class="lab"><span class="dot dn"></span>Build</div><div class="brand">Apex IT Solutions</div>
         <div class="chips"><span class="chip n">Fast, owned site</span><span class="chip n">Technical SEO base</span></div></div>
       <div class="divider"></div>
       <div class="col"><div class="lab"><span class="dot da"></span>Growth</div><div class="brand">Apex Marketings</div>
         <div class="chips"><span class="chip a">Compounding SEO</span><span class="chip a">Ads that convert</span></div></div>
     </div>""",

  """<h2 class="hlg">Stop renting all<br>your <b>growth</b>.</h2>
     <p class="sub">Build the system. Turn it into demand — in that order.</p>
     <div class="ctabox">DM <b>&ldquo;AUDIT&rdquo;</b> and we'll show you what you own vs what you rent, free.</div>""",
]

def render_slide(look, theme, idx, total, inner):
    html = inject(doc(look, theme, idx, total, inner))
    tmp = os.path.join(tempfile.gettempdir(), f"apex_{theme}_{idx}.html")
    with open(tmp, "w", encoding="utf-8") as f: f.write(html)
    raw = os.path.join(tempfile.gettempdir(), f"apex_raw_{theme}_{idx}.png")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
        "--force-device-scale-factor=2", "--default-background-color=00000000",
        "--window-size=%d,%d" % (W, H), "--screenshot=%s" % raw,
        "file:///" + tmp.replace("\\", "/")], check=True, capture_output=True)
    img = Image.open(raw).convert("RGBA")
    import apex_art
    _base = apex_art.palette_for(look, theme)["base"] if look else PALETTES[theme]["base"]
    bg = Image.new("RGBA", img.size, hex_rgb(_base) + (255,))
    img = Image.alpha_composite(bg, img).convert("RGB")
    if img.size != (W, H): img = img.resize((W, H), Image.LANCZOS)
    os.remove(raw)
    return img

def render_slides_lush(slides, kicker, seed):
    """Render the 5 carousel slides in the dark lush look (matches the video).
    Uses the fast_render Chrome (with the GL backend the glassmorphism blur needs),
    one persistent instance for all slides."""
    import base64 as _b64
    from io import BytesIO
    import apex_lush, fast_render as FR
    imgs, ch = [], FR.Chrome()
    try:
        ch.cmd("Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 2, "mobile": False})
        for i, slide in enumerate(slides):
            html = apex_lush.build_lush_slide_html(slide, i + 1, len(slides), kicker, seed, W, H)
            tmp = os.path.join(tempfile.gettempdir(), f"apex_lush_slide_{i + 1}.html")
            with open(tmp, "w", encoding="utf-8") as f: f.write(html)
            ch.cmd("Page.navigate", {"url": "file:///" + tmp.replace("\\", "/")}); ch.wait_load()
            shot = ch.cmd("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
            img = Image.open(BytesIO(_b64.b64decode(shot["data"]))).convert("RGB")
            if img.size != (W, H): img = img.resize((W, H), Image.LANCZOS)
            imgs.append(img)
            print(f"  lush slide {i + 1}/{len(slides)}", flush=True)
    finally:
        ch.close()
    return imgs

LINKEDIN_CAPTION = """Ads rent attention. The day you stop paying, your traffic drops to zero.

Swipe through the 5-slide breakdown.

Most founders pour budget into ads on top of a slow, thin website — scaling the rent on a cracked foundation. A fast, well-structured site + SEO is different: it's an asset you own that compounds month after month, long after the invoice clears.

Fix the asset first. Apex IT builds the fast, owned system; Apex Marketings turns it into compounding demand — in that order.

DM "AUDIT" and we'll show you what you own vs what you rent, free.

If you paused all ad spend tomorrow, how much traffic would you have left?

#SEO #DigitalMarketing #B2BMarketing
"""

FB_CAPTION = """Ads rent attention. Stop paying and your traffic hits zero. 📉

Swipe to see what your ad spend is actually building — rent, or an asset you own.

Most businesses scale the rent (more ads) on a slow site that leaks every click. A fast, well-built site + SEO compounds whether you're spending today or not. Build the system, then turn it into demand.

Save this + DM "AUDIT" for a free look at what you own vs what you rent.

If you paused all ads tomorrow, how much traffic would survive?

#seo #digitalmarketing #googleads #metaads #smallbusinesspakistan #founders #b2bmarketing #websitedesign #leadgeneration #ecommerce #brandbuilding #whatsappbusiness
"""

def cleanup_output():
    for f in os.listdir(OUT):
        p = os.path.join(OUT, f)
        if os.path.isdir(p) and f not in KEEP_DIRS: shutil.rmtree(p)
        elif os.path.isfile(p) and f not in KEEP_FILES: os.remove(p)

# --- optional: load the day's content from a day_spec.json (env APEX_SPEC) ---
import apex_art
LOOK = None
RAW_SLIDES = None   # raw slide dicts (for the lush carousel path; classic path uses SLIDES html)
_spec_path = os.environ.get("APEX_SPEC")
if _spec_path and os.path.exists(_spec_path):
    import apex_spec
    _spec = apex_spec.load(_spec_path)
    LOOK = apex_art.choose_look(_spec, kind="carousel")
    if _spec.get("carousel"):
        _c = _spec["carousel"]
        KICKER = _c["kicker"]
        RAW_SLIDES = _c.get("slides")
        SLIDES = apex_spec.build_carousel_slides(_c, look=LOOK)
        LINKEDIN_CAPTION, FB_CAPTION = apex_spec.carousel_captions(_c)
        print("APEX_SPEC carousel loaded:", _spec.get("id", "?"), "| look:", LOOK["lookbook"], LOOK["theme"], "| lush:", LUSH)

def _save_set(imgs, theme):
    for plat in ("linkedin", "fb"):
        d = os.path.join(OUT, f"{plat}-{theme}")
        os.makedirs(d, exist_ok=True)
        for old in os.listdir(d):
            if old.lower().endswith(".png"): os.remove(os.path.join(d, old))
        for i, im in enumerate(imgs):
            im.save(os.path.join(d, f"{i + 1:02d}.png"), "PNG")
        print("  wrote", f"{plat}-{theme}/ ({len(imgs)} slides)")

if __name__ == "__main__":
    if LOOK is None: LOOK = apex_art.choose_look({}, kind="carousel")
    if LUSH:
        # dark lush carousel (matches the video). Falls back to a fresh local concept if no spec.
        slides, kicker = RAW_SLIDES, KICKER
        if not slides:
            import apex_concept, apex_spec
            _sp = apex_concept.generate()
            slides = _sp["carousel"]["slides"]; kicker = _sp["carousel"]["kicker"]
            LOOK = apex_art.choose_look(_sp, kind="carousel")
            LINKEDIN_CAPTION, FB_CAPTION = apex_spec.carousel_captions(_sp["carousel"])
        print("art-direction: LUSH dark | seed", LOOK["seed"], "| concept", kicker, flush=True)
        imgs = render_slides_lush(slides, kicker, LOOK["seed"])
        _save_set(imgs, "dark")
        for plat in ("linkedin", "fb"):   # drop stale classic light set so the pack is one uniform dark look
            ld = os.path.join(OUT, f"{plat}-light")
            if os.path.isdir(ld): shutil.rmtree(ld)
    else:
        print("art-direction:", LOOK["lookbook"], "| seed", LOOK["seed"], flush=True)
        for theme in ("dark", "light"):
            imgs = [render_slide(LOOK, theme, i + 1, len(SLIDES), inner) for i, inner in enumerate(SLIDES)]
            _save_set(imgs, theme)
    open(os.path.join(OUT, "linkedin.md"), "w", encoding="utf-8").write(LINKEDIN_CAPTION)
    open(os.path.join(OUT, "fb.md"), "w", encoding="utf-8").write(FB_CAPTION)
    cleanup_output()
    apex_art.remember_look(LOOK)
    print("DONE. generated_images now holds:", sorted(os.listdir(OUT)))
