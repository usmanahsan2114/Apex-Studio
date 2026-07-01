# -*- coding: utf-8 -*-
"""
apex_lush.py — "Lush v5" video look: animated 2D VECTOR backgrounds (bubbles / galaxy /
particles / orbits, seeded per video) + per-beat CONCEPT VECTORS related to the headline +
vibrant gradient-mesh color + glassmorphism cards + bold gradient type. Pure SVG/CSS/DOM
(no WebGL), deterministic: the page exposes a pure render(t) (all motion from t — no rAF/
random), captured frame-by-frame by fast_render over CDP.

build_lush_html(aspect, concept, tl) -> full HTML. Reuses build_today_video.ASPECTS + the
VO-driven timeline + Kokoro audio + encode. Brand: amber signature + dual-brand lockup kept;
vibrant color from gradient mesh + tinted vector fields.
"""
import base64, json, math, os, random
import apex_spec

def _hexrgb(h): h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# professionally-dark per-video palettes: deep near-black tonal wash (pos, "r,g,b", alpha)
# + one faint amber glow; muted accent rgb tints for the 2D vector field (light-on-dark, not neon)
PALETTES = [
    dict(name="obsidian", blobs=[("24% 18%", "44,58,92", .20), ("82% 30%", "30,40,70", .16),
                                 ("58% 96%", "255,190,11", .11), ("10% 84%", "26,34,56", .14)],
         tints=["255,206,138", "228,236,255", "150,170,210", "120,140,180"]),
    dict(name="graphite", blobs=[("23% 20%", "52,55,66", .22), ("84% 28%", "38,40,50", .18),
                                 ("57% 95%", "255,190,11", .10), ("9% 83%", "30,32,40", .15)],
         tints=["255,210,150", "236,238,244", "170,176,190", "130,134,148"]),
    dict(name="deep_navy", blobs=[("22% 19%", "26,42,92", .22), ("83% 30%", "34,54,112", .17),
                                  ("58% 95%", "255,190,11", .11), ("10% 85%", "18,28,64", .14)],
         tints=["255,206,138", "224,234,255", "120,150,225", "96,120,190"]),
    dict(name="deep_teal", blobs=[("24% 20%", "14,56,62", .20), ("82% 28%", "18,70,78", .16),
                                  ("57% 96%", "255,190,11", .11), ("11% 84%", "10,40,46", .14)],
         tints=["255,208,140", "224,244,242", "90,200,196", "110,150,160"]),
    dict(name="ink_violet", blobs=[("23% 18%", "42,28,72", .20), ("83% 30%", "56,36,96", .16),
                                   ("58% 95%", "255,190,11", .10), ("9% 84%", "30,20,54", .14)],
         tints=["255,206,138", "232,228,250", "176,150,230", "140,120,190"]),
    dict(name="ember_noir", blobs=[("22% 20%", "70,38,24", .20), ("84% 28%", "92,46,26", .16),
                                   ("58% 95%", "255,190,11", .12), ("10% 84%", "44,26,18", .14)],
         tints=["255,200,130", "246,234,224", "224,150,96", "180,120,90"]),
]
FIELDS = ["bubbles", "galaxy", "particles", "orbits"]

# ---- seeded art direction: one motion personality + accent + texture per video/day ----
# (lock per-day from the seed; this is the lightweight axis engine the design research asked for)
MOTIONS = ["swiss", "editorial", "kinetic", "pulse"]   # easing/stagger/transition feel
ACCENTS = ["beam", "underline", "halo", "ring"]         # how the punch word is emphasised
WIPES = ["left", "right", "up", "diag"]                 # clip-path reveal direction
# curated display+body font pairings (locally-hosted OFL families; the "type system" axis,
# locked per-seed so the carousel and video of a day always share one typographic voice)
PAIRS = [("Archivo", "Inter"), ("Sora", "Manrope"), ("Space Grotesk", "Inter"),
         ("Syne", "Manrope"), ("Fraunces", "Geist"), ("Bricolage Grotesque", "Inter"),
         ("Geist", "Inter"), ("Sora", "Inter")]

def _art(seed, override=None):
    """The day's art axes. Pure seed-derived by default (deterministic). If `override`
    (a pinned `art_direction` from day_spec) is given, its keys win — that's how anti-repeat
    selection (pick_art) is honoured identically by the carousel and the video of one post."""
    r = random.Random((int(seed) or 0) ^ 0x5EED5)
    disp_fam, body_fam = r.choice(PAIRS)
    ad = {
        "motion": r.choice(MOTIONS),
        "accent": r.choice(ACCENTS),
        "wipe": r.choice(WIPES),
        "grain": round(r.uniform(0.62, 0.92), 2),   # feTurbulence baseFrequency (grain coarseness)
        "goct": r.choice([2, 2, 3]),                 # octaves
        "disp": disp_fam, "body": body_fam,          # type pairing (display, body)
    }
    if override:
        for k in list(ad.keys()):
            if override.get(k):
                ad[k] = override[k]
    return ad

def _design_mem_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "design_memory.json")

def pick_art(seed, remember=True):
    """Choose the day's art axes with cross-day ANTI-REPEAT (design_memory.json keeps the last
    few values per axis so consecutive days don't reuse the same motion/accent/type pairing).
    Deterministic given (seed, memory). Call ONCE at concept generation and pin into day_spec
    as `art_direction`; both renderers then read it via _art(seed, art_direction)."""
    try:
        with open(_design_mem_path(), encoding="utf-8") as f:
            mem = json.load(f) or {}
    except Exception:
        mem = {}
    r = random.Random((int(seed) or 0) ^ 0xC0FFEE)
    def pick(axis, options, avoid=2):
        recent = (mem.get(axis) or [])[-avoid:]
        pool = [o for o in options if o not in recent] or list(options)
        return r.choice(pool)
    motion, accent = pick("motion", MOTIONS), pick("accent", ACCENTS)
    pair_i = pick("pair", list(range(len(PAIRS))))
    disp_fam, body_fam = PAIRS[pair_i]
    ad = {"motion": motion, "accent": accent, "wipe": r.choice(WIPES),
          "grain": round(r.uniform(0.62, 0.92), 2), "goct": r.choice([2, 2, 3]),
          "disp": disp_fam, "body": body_fam}
    if remember:
        for axis, val in (("motion", motion), ("accent", accent), ("pair", pair_i)):
            mem[axis] = ((mem.get(axis) or []) + [val])[-6:]
        try:
            with open(_design_mem_path(), "w", encoding="utf-8") as f:
                json.dump(mem, f)
        except Exception:
            pass
    return ad

def _grain_uri(freq, octaves):
    """Seeded SVG fractal-noise (feTurbulence) grain — kills dark-gradient banding + adds
    editorial paper texture. Native browser filter, static across the render loop (deterministic)."""
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'>"
           "<filter id='g'><feTurbulence type='fractalNoise' baseFrequency='%s' numOctaves='%d' stitchTiles='stitch'/>"
           "<feColorMatrix type='saturate' values='0'/></filter>"
           "<rect width='240' height='240' filter='url(#g)'/></svg>" % (freq, int(octaves)))
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

# composition archetypes (seeded, beat-aware): the day's scenes are NOT all the same centered
# card. hero = full-bleed billboard type (no card), rail = left-aligned tension, card = glass card.
# Lockup, pill, progress + safe zones are unchanged regardless of archetype.
def _archetypes(seed, n=6):
    r = random.Random((int(seed) or 0) ^ 0xA12C7)
    out = []
    for i in range(n):
        if i == 0:    out.append(r.choice(["hero", "hero", "card"]))   # hook -> usually billboard
        elif i == 2:  out.append(r.choice(["hero", "card"]))           # peak -> full-bleed type
        elif i == 3:  out.append(r.choice(["rail", "card"]))           # reframe -> editorial rail
        elif i == 5:  out.append(r.choice(["card", "hero"]))           # cta
        else:         out.append("card")                               # problem(1) + fix(4): glass card
    return out

def _slide_arch(seed, idx, total):
    """Archetype for ONE carousel slide (1-based idx). Mirrors the video beat roles:
    1 hook, 2 problem, 3 reframe, 4 fix, 5 cta."""
    r = random.Random((int(seed) or 0) ^ 0xA12C7 ^ (idx * 7))
    if idx == 1:   return r.choice(["hero", "hero", "card"])
    if idx == 3:   return r.choice(["rail", "card"])
    if idx == total: return r.choice(["card", "hero"])
    return "card"

# real 3D depth layer (three.js, software-WebGL, deterministic). Subtle low-poly forms drifting
# in deep space BEHIND the 2D field + glass cards. Gated by APEX_3D (default on for lush);
# fully self-fallback (if three.js fails to load/init, window.T3D stays false and the 2D look stands).
_ENABLE_3D = os.environ.get("APEX_3D", "1") != "0"
def _three_block(seed, P, W, H):
    if not _ENABLE_3D:
        return "", ""
    import build_today_video as V
    try:
        three_src = open(os.path.join(V.ROOT, "assets", "vendor", "three.min.js"), encoding="utf-8").read()
    except Exception:
        return "", ""
    r = random.Random((int(seed) or 0) ^ 0x3D3D3D)
    tints = P["tints"]
    objs = [dict(shape=r.choice(["ico", "oct", "torus", "box", "dodec"]),
                 x=round(r.uniform(-9, 9), 2), y=round(r.uniform(-4, 5), 2), z=round(r.uniform(-18, -7), 2),
                 s=round(r.uniform(0.7, 2.0), 2), rx=round(r.uniform(0.04, 0.26), 3),
                 ry=round(r.uniform(0.04, 0.26), 3), col=r.choice(tints), amp=round(r.uniform(0.3, 0.7), 2))
            for _ in range(7)]
    canvas = '<canvas id="t3d"></canvas>'
    js = ("<script>" + three_src + "</script>\n<script>\n(function(){try{\n"
          "var cv=document.getElementById('t3d');\n"
          "var rnd=new THREE.WebGLRenderer({canvas:cv,antialias:true,alpha:true});\n"
          f"rnd.setSize({W},{H},false); rnd.setPixelRatio(1);\n"
          "var scn=new THREE.Scene(); scn.fog=new THREE.FogExp2(0x06070b,0.05);\n"
          f"var cam=new THREE.PerspectiveCamera(55,{W}/{H},0.1,100); cam.position.set(0,0,9);\n"
          "scn.add(new THREE.AmbientLight(0x44506a,0.75));\n"
          "var dl=new THREE.DirectionalLight(0xffffff,0.55); dl.position.set(3,5,6); scn.add(dl);\n"
          "var pl=new THREE.PointLight(0xffbe0b,1.2,42); pl.position.set(-4,2,5); scn.add(pl);\n"
          "function geom(s){if(s==='ico')return new THREE.IcosahedronGeometry(1,0);"
          "if(s==='oct')return new THREE.OctahedronGeometry(1,0);"
          "if(s==='dodec')return new THREE.DodecahedronGeometry(1,0);"
          "if(s==='torus')return new THREE.TorusGeometry(0.8,0.3,10,28);"
          "return new THREE.BoxGeometry(1.3,1.3,1.3);}\n"
          "var SPEC=" + json.dumps(objs) + ", M=[];\n"
          "for(var i=0;i<SPEC.length;i++){var o=SPEC[i];var c=o.col.split(',').map(Number);\n"
          "var mat=new THREE.MeshStandardMaterial({color:(c[0]<<16)|(c[1]<<8)|c[2],metalness:0.45,roughness:0.55,flatShading:true,transparent:true,opacity:0.62});\n"
          "var me=new THREE.Mesh(geom(o.shape),mat); me.position.set(o.x,o.y,o.z); me.scale.set(o.s,o.s,o.s); me.userData=o; scn.add(me); M.push(me);\n"
          "me.add(new THREE.LineSegments(new THREE.EdgesGeometry(me.geometry),new THREE.LineBasicMaterial({color:0xffd98a,transparent:true,opacity:0.28})));}\n"
          "window.renderThreeScene=function(t){for(var i=0;i<M.length;i++){var o=M[i].userData;\n"
          "M[i].rotation.x=t*o.rx; M[i].rotation.y=t*o.ry; M[i].position.y=o.y+Math.sin(t*0.25+i)*o.amp;}\n"
          "cam.position.x=Math.sin(t*0.08)*1.3; cam.position.y=Math.cos(t*0.07)*0.9; cam.lookAt(0,0,-8); rnd.render(scn,cam);};\n"
          "window.T3D=true;\n}catch(e){window.T3D=false;}})();\n</script>")
    return canvas, js

def _bg(P):
    return ",".join(f"radial-gradient(820px 760px at {pos}, rgba({rgb},{a}), transparent 62%)"
                    for pos, rgb, a in P["blobs"])

# ---------------- animated 2D vector background fields ----------------
def _field(name, P, W, H, rng):
    tints = P["tints"]; el = []
    if name == "bubbles":
        for i in range(26):
            s = rng.randint(46, 200); x = rng.randint(-40, W - 20); y = rng.randint(0, H)
            c = tints[i % len(tints)]; ph = round(rng.uniform(0, 6.28), 2); sp = round(rng.uniform(0.5, 1.4), 2)
            amp = rng.randint(10, 34); b = int(s / 7)
            el.append(f'<div class="fx" data-k="bub" data-ph="{ph}" data-sp="{sp}" data-amp="{amp}" '
                      f'style="left:{x}px;top:{y}px;width:{s}px;height:{s}px;'
                      f'background:radial-gradient(circle at 38% 32%, rgba({c},.40), rgba({c},.05) 58%, transparent 72%);filter:blur({b}px)"></div>')
    elif name == "galaxy":
        cx, cy = W * 0.5, H * 0.40
        for i in range(110):
            a = rng.uniform(0, 6.28); r = rng.uniform(30, max(W, H) * 0.62)
            x = cx + math.cos(a) * r; y = cy + math.sin(a) * r * 0.8
            s = rng.choice([2, 2, 3, 3, 4, 5]); c = "255,255,255" if i % 4 else tints[0]
            ph = round(rng.uniform(0, 6.28), 2)
            el.append(f'<div class="fx" data-k="star" data-ph="{ph}" style="left:{x:.0f}px;top:{y:.0f}px;'
                      f'width:{s}px;height:{s}px;border-radius:50%;background:rgb({c});box-shadow:0 0 {s*3}px rgba({c},.8)"></div>')
    elif name == "particles":
        for i in range(46):
            s = rng.choice([4, 5, 6, 8]); x = rng.randint(0, W); y = rng.randint(0, H)
            c = tints[i % len(tints)]; ph = round(rng.uniform(0, 6.28), 2); sp = round(rng.uniform(0.6, 1.6), 2)
            el.append(f'<div class="fx" data-k="part" data-ph="{ph}" data-sp="{sp}" style="left:{x}px;top:{y}px;'
                      f'width:{s}px;height:{s}px;border-radius:50%;background:rgb({c});box-shadow:0 0 {s*3}px rgba({c},.7)"></div>')
    elif name == "orbits":
        cx, cy = W * 0.5, H * 0.36; c0 = tints[0]; cw = "255,255,255"
        rings = "".join(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r}" fill="none" stroke="rgba({cw},.10)" stroke-width="1.4" stroke-dasharray="3 12"/>'
                        for r in (170, 300, 440, 580))
        svg = f'<svg class="orbsvg" width="{W}" height="{H}" style="position:absolute;inset:0">{rings}</svg>'
        for i in range(16):
            r = (170, 300, 440, 580)[i % 4]; a = rng.uniform(0, 6.28)
            x = cx + math.cos(a) * r; y = cy + math.sin(a) * r
            s = rng.choice([6, 8, 10]); c = tints[i % len(tints)]; sp = round(rng.uniform(0.2, 0.6), 2); ph = round(a, 2)
            el.append(f'<div class="fx" data-k="orb" data-ph="{ph}" data-sp="{sp}" data-r="{r}" '
                      f'style="left:{cx:.0f}px;top:{cy:.0f}px;width:{s}px;height:{s}px;border-radius:50%;'
                      f'background:rgb({c});box-shadow:0 0 {s*2}px rgba({c},.78)"></div>')
        return f'<div class="field" data-field="orbits" data-cx="{cx:.0f}" data-cy="{cy:.0f}">{svg}{"".join(el)}</div>'
    return f'<div class="field" data-field="{name}">{"".join(el)}</div>'

# ---------------- per-beat concept vectors (related to the headline text) ----------------
def _cvec_row(beat):
    try:
        import apex_icons
        names = apex_spec._auto_icon_names(apex_spec._scene_text(beat), 3)
        ics = "".join('<span class="cv" data-i="%d">%s</span>' % (i, apex_icons.icon_svg(n, size=40, cls="ic"))
                      for i, n in enumerate(names))
        return '<div class="cvec">%s</div>' % ics
    except Exception:
        return ""

def _scene_inner(beat):
    parts = [_cvec_row(beat)]
    if beat.get("tag"):
        parts.append('<div class="ltag">%s</div>' % apex_spec._amp(beat["tag"]))
    hl = beat.get("headline", []) or []
    parts.append('<div class="lh">%s</div>' % "<br>".join(
        apex_spec.bold_punch(x, str(beat.get("punch_at", "0.4"))) for x in hl))
    if beat.get("sub"):
        parts.append('<div class="lsub">%s</div>' % apex_spec.bold_static(beat["sub"]))
    mt = beat.get("meter")
    if mt and mt.get("head"):   # animated data-viz metric bar (drawn in render(t))
        parts.append('<div class="lmeter"><div class="lmh">%s</div>'
                     '<div class="lmtrack"><div class="lmfill" data-tgt="84"></div><div class="lmknob" data-tgt="84"></div></div>'
                     '<div class="lmends"><span>%s</span><span class="goal">%s</span></div></div>'
                     % (apex_spec._amp(mt["head"]), apex_spec._amp(mt.get("left", "")), apex_spec._amp(mt.get("right", ""))))
    if beat.get("build_chips") or beat.get("growth_chips"):
        b = "".join('<span class="lchip n">%s</span>' % apex_spec._chip_label(c) for c in beat.get("build_chips", []))
        g = "".join('<span class="lchip a">%s</span>' % apex_spec._chip_label(c) for c in beat.get("growth_chips", []))
        parts.append('<div class="lsplit"><div class="lcol"><div class="lcl">Build &middot; Apex IT</div>'
                     '<div class="lchips">%s</div></div><div class="lcol"><div class="lcl am">Growth &middot; Apex Mktg</div>'
                     '<div class="lchips">%s</div></div></div>' % (b, g))
    if beat.get("cta"):
        parts.append('<div class="lcta">%s</div>' % apex_spec._cta(beat["cta"]))
    return "".join(parts)

def build_lush_html(aspect, concept, tl):
    import build_today_video as V
    A = V.ASPECTS[aspect]; W, H = A["w"], A["h"]
    look = concept.get("look") or {}
    seed = int(look.get("seed", 0) or 0)
    AD = _art(seed, concept.get("art")); GR = _grain_uri(AD["grain"], AD["goct"])
    import apex_art
    ff = apex_art.fontface_css({"fonts": {"display": AD["disp"], "body": AD["body"]}})  # @font-face (seed-locked pairing)
    disp = apex_art._font_stack(AD["disp"])   # premium display face (headline)
    body = apex_art._font_stack(AD["body"])   # body face (sub/labels)
    rng = random.Random(seed ^ 0xABCDEF)
    P = PALETTES[rng.randrange(len(PALETTES))]
    field_name = os.environ.get("APEX_FIELD") if os.environ.get("APEX_FIELD") in FIELDS else rng.choice(FIELDS)
    field_html = _field(field_name, P, W, H, random.Random(seed ^ 0xF1E1D))
    t3d_canvas, t3d_js = _three_block(seed, P, W, H)   # real 3D depth layer (behind field); "" if disabled/failed
    beats = (concept.get("raw_video") or {}).get("scenes") or []
    if not beats:
        beats = [{"headline": [s]} for s in concept.get("scenes", [])]
    # big floating concept vectors (related to the overall topic) in the open upper area
    topic_text = (concept.get("raw_video") or {}).get("caption", "") + " " + " ".join(
        " ".join(b.get("headline", [])) for b in beats)
    try:
        import apex_icons
        big_names = apex_spec._auto_icon_names(topic_text or concept.get("kicker", ""), 4)
        bigs = []
        for i, n in enumerate(big_names):
            a = i * 2.39996323
            x = int(W * (0.5 + 0.40 * math.cos(a))); y = int(H * (0.26 + 0.17 * math.sin(a * 1.7)))
            sz = 78 + (i % 3) * 26
            bigs.append('<span class="bvec" data-i="%d" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx">%s</span>'
                        % (i, x, y, sz, sz, apex_icons.icon_svg(n, size=sz, cls="ic", accent=(i % 2 == 0))))
        bigvec_html = '<div class="bigvec-wrap">%s</div>' % "".join(bigs)
    except Exception:
        bigvec_html = ""
    arch = _archetypes(seed, len(beats[:6]))
    scene_divs = "\n".join(
        f'<div class="scene arch-{arch[i]}" id="s{i+1}"><div class="card">{_scene_inner(b)}</div></div>'
        for i, b in enumerate(beats[:6]))
    kicker = concept.get("kicker", "Apex")
    # burned sound-off captions: per-beat voiceover line, revealed word-by-word (deterministic)
    _CAPS = os.environ.get("APEX_CAPTIONS", "1") != "0"
    narr = (concept.get("raw_video") or {}).get("narration") or []
    cap_html = ""
    if _CAPS and narr:
        def _cw(txt):
            return " ".join('<span class="cw">%s</span>' % apex_spec._amp(w) for w in str(txt).split())
        cap_html = '<div class="capwrap">%s</div>' % "".join(
            '<div class="cap" id="cap%d">%s</div>' % (i + 1, _cw(n.get("text", ""))) for i, n in enumerate(narr[:6]))
    cz_bottom = A['safe_bottom'] + (256 if cap_html else 98)   # raise the card to clear the caption band
    style = f"""
*{{margin:0;box-sizing:border-box}}
{ff}
html,body{{width:{W}px;height:{H}px;overflow:hidden;font-family:{body}}}
.stage{{position:relative;width:{W}px;height:{H}px;background:#06070b;overflow:hidden}}
#t3d{{position:absolute;inset:0;z-index:0;pointer-events:none}}
.mesh{{position:absolute;inset:-12%;background:{_bg(P)};filter:saturate(0.9) brightness(0.92);will-change:transform}}
.field{{position:absolute;inset:0;z-index:1;pointer-events:none;transform-origin:50% 40%}}
.field .fx{{position:absolute;will-change:transform,opacity}}
.vign{{position:absolute;inset:0;z-index:2;background:radial-gradient(135% 105% at 50% 40%, transparent 52%, rgba(0,0,0,.74) 100%)}}
.grain{{position:absolute;inset:0;z-index:2;opacity:.07;mix-blend-mode:overlay;background:url('{GR}')}}
.bigvec-wrap{{position:absolute;inset:0;z-index:3;pointer-events:none}}
.bvec{{position:absolute;transform:translate(-50%,-50%);color:#FFD98A;filter:drop-shadow(0 0 14px rgba(255,200,90,.7));opacity:.5}}
.bvec .ic.accent{{color:#FFFFFF}}
.pill{{position:absolute;z-index:5;top:{A['safe_top']+30}px;left:60px;padding:13px 22px;border-radius:999px;font-size:16px;font-weight:800;
 letter-spacing:3px;text-transform:uppercase;color:#fff;background:rgba(255,255,255,.10);
 backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,.22)}}
.cardzone{{position:absolute;z-index:4;left:56px;right:56px;top:{A['safe_top']+128}px;bottom:{cz_bottom}px}}
.capwrap{{position:absolute;z-index:5;left:64px;right:64px;bottom:{A['safe_bottom']+92}px;height:150px;display:flex;align-items:flex-end;justify-content:center;pointer-events:none}}
.cap{{position:absolute;left:0;right:0;bottom:0;text-align:center;font-size:29px;font-weight:600;line-height:1.34;letter-spacing:-0.2px;color:rgba(255,255,255,.97);text-shadow:0 2px 16px rgba(0,0,0,.92);display:none}}
.cap .cw{{display:inline-block;opacity:0;will-change:opacity,transform}}
.scene{{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:flex-end}}
.scene.arch-rail{{align-items:flex-start}}
.scene.arch-hero{{justify-content:center;align-items:center;text-align:center}}
.card{{position:relative;padding:48px 50px;border-radius:36px;
 background:linear-gradient(160deg, rgba(255,255,255,.13), rgba(255,255,255,.04));
 backdrop-filter:blur(28px) saturate(1.3);-webkit-backdrop-filter:blur(28px) saturate(1.3);
 border:1px solid rgba(255,255,255,.22);box-shadow:0 44px 110px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.28);will-change:transform,opacity}}
.arch-rail .card{{max-width:90%}}
.arch-hero .card{{background:radial-gradient(120% 88% at 50% 46%, rgba(6,7,11,.62), rgba(6,7,11,.28) 58%, transparent 80%);border:none;box-shadow:none;backdrop-filter:none;-webkit-backdrop-filter:none;padding:34px 28px;max-width:94%}}
.arch-hero .lh{{font-size:{int(A['lg']*1.12)}px;letter-spacing:-2.4px}}
.arch-hero .cvec{{justify-content:center}}
.cvec{{display:flex;gap:16px;margin-bottom:20px}}
.cvec .cv{{display:inline-flex;align-items:center;justify-content:center;width:62px;height:62px;border-radius:16px;
 background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.2);color:#FFD98A;
 box-shadow:0 8px 22px rgba(0,0,0,.3);will-change:transform,opacity}}
.cvec .cv:nth-child(2){{color:#fff}}
.cvec .cv .ic{{width:38px;height:38px}}
.ltag{{font-size:17px;font-weight:800;letter-spacing:4px;text-transform:uppercase;color:#FFD66B;margin-bottom:16px}}
.lh{{font-family:{disp};font-size:{int(A['lg']*0.92)}px;font-weight:900;line-height:1.0;letter-spacing:-1.8px;color:#fff;text-shadow:0 6px 36px rgba(0,0,0,.45);text-wrap:balance}}
.lh b{{color:#FFC21E}} .lh b.punch{{background:linear-gradient(90deg,#FFD54A,#FF8A3D);-webkit-background-clip:text;background-clip:text;color:transparent}}
.acc-halo .lh b.punch{{filter:drop-shadow(0 0 22px rgba(255,190,11,.45))}}
.acc-beam .arch-card>.card,.acc-beam .arch-rail>.card{{border-left:3px solid rgba(255,190,11,.55)}}
.acc-underline .lh{{padding-bottom:8px;border-bottom:2px solid rgba(255,190,11,.32)}}
.acc-ring .arch-card>.card,.acc-ring .arch-rail>.card{{outline:1px solid rgba(255,190,11,.22);outline-offset:-1px}}
.lsub{{margin-top:22px;font-size:{A['sub']-2}px;font-weight:500;line-height:1.4;color:rgba(255,255,255,.85);max-width:820px}}
.lsub b{{color:#fff;font-weight:700}}
.lmeter{{margin-top:24px}}
.lmh{{font-size:15px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:rgba(255,255,255,.68);margin-bottom:12px}}
.lmtrack{{height:8px;border-radius:5px;background:rgba(255,255,255,.12);position:relative}}
.lmfill{{position:absolute;left:0;top:0;bottom:0;width:0;border-radius:5px;background:linear-gradient(90deg,#fff,#FFBE0B)}}
.lmknob{{position:absolute;left:0;top:50%;width:15px;height:15px;border-radius:50%;background:#FFBE0B;transform:translate(-50%,-50%);box-shadow:0 0 14px #FFBE0B}}
.lmends{{display:flex;justify-content:space-between;margin-top:12px;font-size:{A['sub']-10}px;font-weight:600;color:rgba(255,255,255,.78)}}
.lmends .goal{{color:#FFC21E}}
.lsplit{{margin-top:28px;display:grid;grid-template-columns:1fr 1fr;gap:26px}}
.lcl{{font-size:18px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:#fff;margin-bottom:14px}} .lcl.am{{color:#FFC21E}}
.lchips{{display:flex;flex-wrap:wrap;gap:10px}}
.lchip{{font-size:16px;font-weight:700;padding:11px 16px;border-radius:12px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.18);color:#fff}}
.lchip.a{{border-color:rgba(255,190,11,.55);color:#FFD98A}}
.lcta{{margin-top:24px;font-size:{A['sub']-2}px;font-weight:600;color:rgba(255,255,255,.9)}} .lcta b{{color:#FFC21E;font-weight:800}}
.lock{{position:absolute;z-index:5;left:0;right:0;bottom:{A['safe_bottom']+54}px;display:flex;align-items:center;justify-content:center;gap:15px;
 font-size:19px;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;color:#fff}}
.lock .dot{{width:8px;height:8px;border-radius:50%;background:#FFBE0B;box-shadow:0 0 14px #FFBE0B}}
.pbarw{{position:absolute;z-index:5;left:60px;right:60px;bottom:{A['safe_bottom']+30}px;height:3px;background:rgba(255,255,255,.14);border-radius:3px;overflow:hidden}}
.pbar{{height:100%;width:0;background:linear-gradient(90deg,#fff,#FFBE0B)}}
"""
    body = f"""
<div class="stage acc-{AD['accent']}">
 <div class="mesh"></div>
 {t3d_canvas}
 {field_html}
 <div class="vign"></div><div class="grain"></div>
 {bigvec_html}
 <div class="pill">{kicker}</div>
 <div class="cardzone">{scene_divs}</div>
 {cap_html}
 <div class="lock"><span>APEX IT SOLUTIONS</span><span class="dot"></span><span>APEX MARKETINGS</span></div>
 <div class="pbarw"><div class="pbar"></div></div>
</div>
{t3d_js}
<script>
var W={W},H={H},TL={json.dumps(tl)};
var MOTION={json.dumps(AD['motion'])},WIPE={json.dumps(AD['wipe'])};
function c01(x){{return x<0?0:x>1?1:x;}}
function lerp(a,b,u){{return a+(b-a)*u;}}
function eOut(u){{return 1-Math.pow(1-u,3);}}
function eIn(u){{return u*u;}}
function eOutQ(u){{return 1-Math.pow(1-u,4);}}
function eInOut(u){{return u<0.5?4*u*u*u:1-Math.pow(-2*u+2,3)/2;}}
function easeEnter(u){{return MOTION==='editorial'?eInOut(u):(MOTION==='kinetic'?eOutQ(u):eOut(u));}}
var ENT=MOTION==='editorial'?0.72:(MOTION==='kinetic'?0.40:(MOTION==='pulse'?0.52:0.55));
var STAG=MOTION==='kinetic'?0.14:(MOTION==='editorial'?0.05:0.10);
function wipeClip(u){{var p=100*(1-u);
  if(WIPE==='left')return 'inset(0 '+p.toFixed(1)+'% 0 0 round 36px)';
  if(WIPE==='right')return 'inset(0 0 0 '+p.toFixed(1)+'% round 36px)';
  if(WIPE==='up')return 'inset('+p.toFixed(1)+'% 0 0 0 round 36px)';
  return 'inset('+(p*0.62).toFixed(1)+'% '+(p*0.62).toFixed(1)+'% 0 0 round 36px)';}}
// kinetic data-viz: numeric punch words count up (Rs 0 -> Rs 90,000 ; 0% -> 50% ; 0 -> 1,000)
function parseNum(s){{var m=s.match(/^([^0-9]*)([0-9][0-9,]*)(.*)$/);if(!m)return null;
  var d=m[2];return {{pre:m[1],n:parseInt(d.replace(/,/g,''),10),suf:m[3],comma:d.indexOf(',')>=0}};}}
function fmtNum(n,c){{return c?n.toLocaleString('en-US'):(''+n);}}
var ALLPUNCH=document.querySelectorAll('.punch');
for(var _p=0;_p<ALLPUNCH.length;_p++){{ALLPUNCH[_p].setAttribute('data-final',ALLPUNCH[_p].textContent);}}
var FXL=document.querySelectorAll('.field .fx');
var FIELD=document.querySelector('.field'); var FN=FIELD?FIELD.getAttribute('data-field'):'';
var CX=FIELD?+(FIELD.getAttribute('data-cx')||0):0, CY=FIELD?+(FIELD.getAttribute('data-cy')||0):0;
function activeBeat(t){{var aI=-1,aP=0; for(var i=0;i<TL.scenes.length;i++){{var s=TL.scenes[i];var lo=t-s.start,ln=s.end-s.start;
  if(lo>=-0.3&&lo<=ln+0.05){{aI=i;aP=c01(lo/ln);}}}} return [aI,aP];}}
function animField(t){{
  if(FN==='galaxy'&&FIELD)FIELD.style.transform='rotate('+(t*0.9).toFixed(2)+'deg)';
  for(var i=0;i<FXL.length;i++){{var el=FXL[i],k=el.getAttribute('data-k'),ph=+el.getAttribute('data-ph');
    if(k==='bub'){{var sp=+el.getAttribute('data-sp'),amp=+el.getAttribute('data-amp');
      var dy=-(((t*sp*34)%(H+280)));
      el.style.transform='translate('+(Math.sin(t*0.5+ph)*amp).toFixed(1)+'px,'+dy.toFixed(1)+'px)';
      el.style.opacity=(0.22+0.24*Math.abs(Math.sin(t*0.5+ph))).toFixed(3);}}
    else if(k==='star'){{el.style.opacity=(0.25+0.55*Math.abs(Math.sin(t*1.2+ph))).toFixed(3);}}
    else if(k==='part'){{var sp2=+el.getAttribute('data-sp');var d=((t*sp2*42)%(W+200));
      el.style.transform='translate('+d.toFixed(1)+'px,'+(-d*0.55).toFixed(1)+'px)';
      el.style.opacity=(0.18+0.30*Math.sin(t*0.7+ph)).toFixed(3);}}
    else if(k==='orb'){{var sp3=+el.getAttribute('data-sp'),r=+el.getAttribute('data-r');var ang=ph+t*sp3;
      el.style.transform='translate('+(Math.cos(ang)*r).toFixed(1)+'px,'+(Math.sin(ang)*r).toFixed(1)+'px)';}}
  }}
  var os2=document.querySelector('.orbsvg'); if(os2&&FN==='orbits')os2.style.transform='rotate('+(t*4).toFixed(2)+'deg)';
}}
function render(t){{
 var ab=activeBeat(t),aI=ab[0],aP=ab[1];
 if(window.renderThreeScene){{try{{renderThreeScene(t);}}catch(e){{}}}}
 animField(t);
 var mz=document.querySelector('.mesh'); if(mz)mz.style.transform='translate('+(Math.sin(t*0.13)*22).toFixed(1)+'px,'+(Math.cos(t*0.11)*18).toFixed(1)+'px)';
 var pb=document.querySelector('.pbar'); if(pb)pb.style.width=(c01(t/TL.total)*100)+'%';
 var intro=eOut(c01(t/0.5)); var pl=document.querySelector('.pill'); if(pl)pl.style.opacity=intro;
 var lk=document.querySelector('.lock'); if(lk)lk.style.opacity=eOut(c01((t-0.2)/0.5));
 var bv=document.querySelectorAll('.bvec');
 for(var b2=0;b2<bv.length;b2++){{var bp=b2*1.4;
   bv[b2].style.transform='translate(-50%,-50%) translate('+(Math.sin(t*0.35+bp)*26).toFixed(1)+'px,'+(Math.cos(t*0.3+bp)*22).toFixed(1)+'px) rotate('+(Math.sin(t*0.4+bp)*12).toFixed(1)+'deg)';
   bv[b2].style.opacity=(intro*(0.34+0.26*Math.abs(Math.sin(t*0.5+bp)))).toFixed(3);}}
 for(var i=0;i<TL.scenes.length;i++){{
   var s=TL.scenes[i],el=document.getElementById('s'+(i+1)); if(!el)continue;
   var card=el.querySelector('.card')||el;
   var lo=t-s.start,ln=s.end-s.start;
   if(lo<-0.3||lo>ln+0.05){{el.style.display='none';continue;}}
   el.style.display='flex';
   var en=easeEnter(c01(lo/ENT)), ex=eIn(c01((lo-(ln-0.42))/0.42));
   card.style.opacity=(c01(lo/0.16)*(1-ex)).toFixed(3);
   card.style.clipPath=wipeClip(en);
   card.style.transform='translateY('+((1-en)*(MOTION==='kinetic'?34:22) - ex*26).toFixed(1)+'px) scale('+(lerp(0.965,1,en)-ex*0.04).toFixed(3)+')';
   var cv=el.querySelectorAll('.cvec .cv');
   for(var ci=0;ci<cv.length;ci++){{var cu=easeEnter(c01((lo-0.18-ci*STAG)/0.5));
     cv[ci].style.opacity=cu.toFixed(3);
     cv[ci].style.transform='translateY('+((1-cu)*16).toFixed(1)+'px) scale('+lerp(0.6,1,cu).toFixed(3)+') rotate('+(Math.sin(t*0.8+ci)*4).toFixed(1)+'deg)';}}
   var pn=el.querySelectorAll('.punch');
   for(var m=0;m<pn.length;m++){{var at=parseFloat(pn[m].getAttribute('data-at')||'0.4');var pu=eOut(c01((lo-at)/0.5));
     pn[m].style.display='inline-block';pn[m].style.transform='scale('+lerp(0.7,1,pu).toFixed(3)+')';
     var fin=pn[m].getAttribute('data-final');var pd=fin?parseNum(fin):null;
     if(pd){{var cuN=eOut(c01((lo-at)/0.78));pn[m].textContent=pd.pre+fmtNum(Math.round(pd.n*cuN),pd.comma)+pd.suf;}}}}
   var mf=el.querySelector('.lmfill');   // animated data-viz metric bar
   if(mf){{var tg=+mf.getAttribute('data-tgt')||84;var mu=eOut(c01((lo-0.35)/0.9));
     mf.style.width=(tg*mu).toFixed(1)+'%';var mk=el.querySelector('.lmknob');if(mk)mk.style.left=(tg*mu).toFixed(1)+'%';}}
 }}
 var caps=document.querySelectorAll('.cap');   // burned VO captions: word-by-word reveal per beat
 for(var qi=0;qi<caps.length;qi++){{var cs=TL.scenes[qi];
   if(!cs){{caps[qi].style.display='none';continue;}}
   var clo=t-cs.start,cln=cs.end-cs.start;
   if(clo<-0.15||clo>cln+0.05){{caps[qi].style.display='none';continue;}}
   caps[qi].style.display='block';
   var cw=caps[qi].querySelectorAll('.cw');var cspan=cln*0.62;
   for(var wq=0;wq<cw.length;wq++){{var wt=0.25+(wq/Math.max(1,cw.length))*cspan;
     var wu=eOut(c01((clo-wt)/0.34));var wex=eIn(c01((clo-(cln-0.35))/0.35));
     cw[wq].style.opacity=(wu*(1-wex)).toFixed(3);
     cw[wq].style.transform='translateY('+((1-wu)*9).toFixed(1)+'px)';}}
 }}
}}
function getT(){{var p=new URLSearchParams(location.search);var v=parseFloat(p.get('t'));return isNaN(v)?0:v;}}
render(getT());
</script>"""
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{style}</style></head><body>{body}</body></html>"

# ---------------- static single-slide build (CAROUSEL, dark lush) ----------------
def _slide_inner(slide):
    """Card content for ONE carousel slide dict (headline/sub/tag/motif/meter/chips/cta)."""
    parts = [_cvec_row(slide)]
    if slide.get("motif"):
        parts.append('<div class="lstamp">%s</div>' % apex_spec._arrowify(str(slide["motif"])))
    if slide.get("tag"):
        parts.append('<div class="ltag">%s</div>' % apex_spec._amp(slide["tag"]))
    hl = slide.get("headline", []) or []
    parts.append('<div class="lh">%s</div>' % "<br>".join(apex_spec.bold_static(x) for x in hl))
    if slide.get("sub"):
        parts.append('<div class="lsub">%s</div>' % apex_spec.bold_static(slide["sub"]))
    mt = slide.get("meter")
    if mt and mt.get("head"):
        parts.append('<div class="lmeter"><div class="lmh">%s</div>'
                     '<div class="lmtrack"><div class="lmfill"></div><div class="lmknob"></div></div>'
                     '<div class="lmends"><span>%s</span><span class="goal">%s</span></div></div>'
                     % (apex_spec._amp(mt["head"]), apex_spec._amp(mt.get("left", "")), apex_spec._amp(mt.get("right", ""))))
    if slide.get("build_chips") or slide.get("growth_chips"):
        b = "".join('<span class="lchip n">%s</span>' % apex_spec._chip_label(c) for c in slide.get("build_chips", []))
        g = "".join('<span class="lchip a">%s</span>' % apex_spec._chip_label(c) for c in slide.get("growth_chips", []))
        parts.append('<div class="lsplit"><div class="lcol"><div class="lcl">Build &middot; Apex IT</div>'
                     '<div class="lchips">%s</div></div><div class="lcol"><div class="lcl am">Growth &middot; Apex Mktg</div>'
                     '<div class="lchips">%s</div></div></div>' % (b, g))
    if slide.get("cta"):
        parts.append('<div class="lcta">%s</div>' % apex_spec._cta(slide["cta"]))
    return "".join(parts)

def build_lush_slide_html(slide, idx, total, kicker, seed, W=1080, H=1350, look=None, art=None):
    """Static single carousel slide in the dark lush look. Reuses the SAME seeded palette +
    field + art direction (grain/accent/fonts) as the video, so the carousel and video read
    as one campaign. Frozen (no render(t)), with carousel slide copy + a slide-position bar."""
    import build_today_video as V, apex_art
    seed = int(seed or 0)
    AD = _art(seed, art)
    arch = _slide_arch(seed, idx, total)
    ff = apex_art.fontface_css({"fonts": {"display": AD["disp"], "body": AD["body"]}})
    disp = apex_art._font_stack(AD["disp"])
    body = apex_art._font_stack(AD["body"])
    rng = random.Random(seed ^ 0xABCDEF)
    P = PALETTES[rng.randrange(len(PALETTES))]
    field_name = os.environ.get("APEX_FIELD") if os.environ.get("APEX_FIELD") in FIELDS else rng.choice(FIELDS)
    field_html = _field(field_name, P, W, H, random.Random(seed ^ 0xF1E1D))
    try:
        import apex_icons
        names = apex_spec._auto_icon_names(" ".join(slide.get("headline", []) or []) or kicker, 3)
        bigs = []
        for i, n in enumerate(names):
            a = i * 2.39996323
            x = int(W * (0.5 + 0.34 * math.cos(a))); y = int(H * (0.20 + 0.12 * math.sin(a * 1.7)))
            sz = 70 + (i % 3) * 22
            bigs.append('<span class="bvec" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx">%s</span>'
                        % (x, y, sz, sz, apex_icons.icon_svg(n, size=sz, cls="ic", accent=(i % 2 == 0))))
        bigvec_html = '<div class="bigvec-wrap">%s</div>' % "".join(bigs)
    except Exception:
        bigvec_html = ""
    dots = "".join('<span class="pd%s"></span>' % (" on" if i + 1 == idx else "") for i in range(total))
    GR = _grain_uri(AD["grain"], AD["goct"])
    inner = _slide_inner(slide)
    style = f"""
*{{margin:0;box-sizing:border-box}}
{ff}
html,body{{width:{W}px;height:{H}px;overflow:hidden;font-family:{body}}}
.stage{{position:relative;width:{W}px;height:{H}px;background:#06070b;overflow:hidden}}
.mesh{{position:absolute;inset:-12%;background:{_bg(P)};filter:saturate(0.9) brightness(0.92)}}
.field{{position:absolute;inset:0;z-index:1;pointer-events:none}}
.field .fx{{position:absolute;opacity:.5}}
.field .fx[data-k="bub"]{{opacity:.32}}
.field .fx[data-k="star"]{{opacity:.6}}
.vign{{position:absolute;inset:0;z-index:2;background:radial-gradient(135% 105% at 50% 40%, transparent 52%, rgba(0,0,0,.74) 100%)}}
.grain{{position:absolute;inset:0;z-index:2;opacity:.07;mix-blend-mode:overlay;background:url('{GR}')}}
.bigvec-wrap{{position:absolute;inset:0;z-index:3;pointer-events:none}}
.bvec{{position:absolute;transform:translate(-50%,-50%);color:#FFD98A;filter:drop-shadow(0 0 14px rgba(255,200,90,.6));opacity:.42}}
.bvec .ic.accent{{color:#fff}}
.pill{{position:absolute;z-index:5;top:54px;left:56px;padding:13px 22px;border-radius:999px;font-size:16px;font-weight:800;letter-spacing:3px;text-transform:uppercase;color:#fff;background:rgba(255,255,255,.10);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,.22)}}
.cardzone{{position:absolute;z-index:4;left:56px;right:56px;top:280px;bottom:190px;display:flex;flex-direction:column;justify-content:center}}
.scene{{position:relative;width:100%;display:flex;flex-direction:column;justify-content:center}}
.scene.arch-rail{{align-items:flex-start}}
.scene.arch-hero{{align-items:center;text-align:center}}
.card{{position:relative;padding:46px 48px;border-radius:34px;background:linear-gradient(160deg, rgba(255,255,255,.13), rgba(255,255,255,.04));backdrop-filter:blur(28px) saturate(1.3);-webkit-backdrop-filter:blur(28px) saturate(1.3);border:1px solid rgba(255,255,255,.22);box-shadow:0 40px 100px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.28)}}
.arch-rail .card{{max-width:92%}}
.arch-hero .card{{background:none;border:none;box-shadow:none;backdrop-filter:none;-webkit-backdrop-filter:none;padding:0 8px;max-width:96%}}
.arch-hero .lh{{font-size:74px;letter-spacing:-2px}}
.arch-hero .cvec{{justify-content:center}}
.cvec{{display:flex;gap:14px;margin-bottom:18px}}
.cvec .cv{{display:inline-flex;align-items:center;justify-content:center;width:58px;height:58px;border-radius:15px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.2);color:#FFD98A;box-shadow:0 8px 22px rgba(0,0,0,.3)}}
.cvec .cv:nth-child(2){{color:#fff}}
.cvec .cv .ic{{width:34px;height:34px}}
.lstamp{{display:inline-flex;align-items:center;font-size:16px;font-weight:700;letter-spacing:.4px;color:rgba(255,255,255,.8);margin-bottom:14px}}
.lstamp .arr{{color:#FFC21E;font-weight:800;padding:0 8px}}
.ltag{{font-size:16px;font-weight:800;letter-spacing:4px;text-transform:uppercase;color:#FFD66B;margin-bottom:14px}}
.lh{{font-family:{disp};font-size:62px;font-weight:900;line-height:1.02;letter-spacing:-1.4px;color:#fff;text-shadow:0 6px 36px rgba(0,0,0,.45);text-wrap:balance}}
.lh b{{color:#FFC21E}}
.acc-halo .lh b{{filter:drop-shadow(0 0 18px rgba(255,190,11,.4))}}
.acc-beam .arch-card>.card,.acc-beam .arch-rail>.card{{border-left:3px solid rgba(255,190,11,.55)}}
.acc-underline .lh{{padding-bottom:8px;border-bottom:2px solid rgba(255,190,11,.32)}}
.acc-ring .arch-card>.card,.acc-ring .arch-rail>.card{{outline:1px solid rgba(255,190,11,.22);outline-offset:-1px}}
.lsub{{margin-top:22px;font-size:30px;font-weight:500;line-height:1.42;color:rgba(255,255,255,.85)}}
.lsub b{{color:#fff;font-weight:700}}
.lmeter{{margin-top:28px}}
.lmh{{font-size:15px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:rgba(255,255,255,.7);margin-bottom:12px}}
.lmtrack{{height:8px;border-radius:5px;background:rgba(255,255,255,.12);position:relative}}
.lmfill{{position:absolute;left:0;top:0;bottom:0;width:84%;border-radius:5px;background:linear-gradient(90deg,#fff,#FFBE0B)}}
.lmknob{{position:absolute;left:84%;top:50%;width:15px;height:15px;border-radius:50%;background:#FFBE0B;transform:translate(-50%,-50%);box-shadow:0 0 14px #FFBE0B}}
.lmends{{display:flex;justify-content:space-between;margin-top:12px;font-size:18px;font-weight:600;color:rgba(255,255,255,.78)}}
.lmends .goal{{color:#FFC21E}}
.lsplit{{margin-top:26px;display:grid;grid-template-columns:1fr 1fr;gap:24px}}
.lcl{{font-size:18px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:#fff;margin-bottom:13px}}
.lcl.am{{color:#FFC21E}}
.lchips{{display:flex;flex-wrap:wrap;gap:10px}}
.lchip{{font-size:16px;font-weight:700;padding:11px 16px;border-radius:12px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.18);color:#fff}}
.lchip.a{{border-color:rgba(255,190,11,.55);color:#FFD98A}}
.lcta{{margin-top:24px;font-size:28px;font-weight:600;line-height:1.4;color:rgba(255,255,255,.9)}}
.lcta b{{color:#FFC21E;font-weight:800}}
.dind{{position:absolute;z-index:5;left:0;right:0;bottom:128px;display:flex;gap:10px;align-items:center;justify-content:center}}
.dind .pd{{width:9px;height:9px;border-radius:50%;background:rgba(255,255,255,.28)}}
.dind .pd.on{{width:28px;border-radius:5px;background:#FFBE0B;box-shadow:0 0 14px #FFBE0B}}
.lock{{position:absolute;z-index:5;left:0;right:0;bottom:64px;display:flex;align-items:center;justify-content:center;gap:15px;font-size:19px;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;color:#fff}}
.lock .dot{{width:8px;height:8px;border-radius:50%;background:#FFBE0B;box-shadow:0 0 14px #FFBE0B}}
"""
    body = (f'<div class="stage acc-{AD["accent"]}"><div class="mesh"></div>{field_html}'
            f'<div class="vign"></div><div class="grain"></div>{bigvec_html}'
            f'<div class="pill">{apex_spec._amp(kicker)}</div>'
            f'<div class="cardzone"><div class="scene arch-{arch}"><div class="card">{inner}</div></div></div>'
            f'<div class="dind">{dots}</div>'
            f'<div class="lock"><span>APEX IT SOLUTIONS</span><span class="dot"></span><span>APEX MARKETINGS</span></div>'
            f'</div>')
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{style}</style></head><body>{body}</body></html>"
