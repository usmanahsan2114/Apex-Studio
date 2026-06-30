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
import json, math, os, random
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
    rng = random.Random(seed ^ 0xABCDEF)
    P = PALETTES[rng.randrange(len(PALETTES))]
    field_name = os.environ.get("APEX_FIELD") if os.environ.get("APEX_FIELD") in FIELDS else rng.choice(FIELDS)
    field_html = _field(field_name, P, W, H, random.Random(seed ^ 0xF1E1D))
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
    scene_divs = "\n".join(f'<div class="scene" id="s{i+1}">{_scene_inner(b)}</div>' for i, b in enumerate(beats[:6]))
    kicker = concept.get("kicker", "Apex")
    style = f"""
*{{margin:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;font-family:'Segoe UI','Inter',Arial,sans-serif}}
.stage{{position:relative;width:{W}px;height:{H}px;background:#06070b;overflow:hidden}}
.mesh{{position:absolute;inset:-12%;background:{_bg(P)};filter:saturate(0.9) brightness(0.92);will-change:transform}}
.field{{position:absolute;inset:0;z-index:1;pointer-events:none;transform-origin:50% 40%}}
.field .fx{{position:absolute;will-change:transform,opacity}}
.vign{{position:absolute;inset:0;z-index:2;background:radial-gradient(135% 105% at 50% 40%, transparent 52%, rgba(0,0,0,.74) 100%)}}
.grain{{position:absolute;inset:0;z-index:2;opacity:.05;mix-blend-mode:overlay;background:url('{V.pack.GRAIN}')}}
.bigvec-wrap{{position:absolute;inset:0;z-index:3;pointer-events:none}}
.bvec{{position:absolute;transform:translate(-50%,-50%);color:#FFD98A;filter:drop-shadow(0 0 14px rgba(255,200,90,.7));opacity:.5}}
.bvec .ic.accent{{color:#FFFFFF}}
.pill{{position:absolute;z-index:5;top:{A['safe_top']+30}px;left:60px;padding:13px 22px;border-radius:999px;font-size:16px;font-weight:800;
 letter-spacing:3px;text-transform:uppercase;color:#fff;background:rgba(255,255,255,.10);
 backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,.22)}}
.cardzone{{position:absolute;z-index:4;left:56px;right:56px;bottom:{A['safe_bottom']+150}px;height:{int(H*0.42)}px}}
.scene{{position:absolute;left:0;right:0;bottom:0;padding:48px 50px;border-radius:36px;
 background:linear-gradient(160deg, rgba(255,255,255,.13), rgba(255,255,255,.04));
 backdrop-filter:blur(28px) saturate(1.3);-webkit-backdrop-filter:blur(28px) saturate(1.3);
 border:1px solid rgba(255,255,255,.22);box-shadow:0 44px 110px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.28);will-change:transform,opacity}}
.cvec{{display:flex;gap:16px;margin-bottom:20px}}
.cvec .cv{{display:inline-flex;align-items:center;justify-content:center;width:62px;height:62px;border-radius:16px;
 background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.2);color:#FFD98A;
 box-shadow:0 8px 22px rgba(0,0,0,.3);will-change:transform,opacity}}
.cvec .cv:nth-child(2){{color:#fff}}
.cvec .cv .ic{{width:38px;height:38px}}
.ltag{{font-size:17px;font-weight:800;letter-spacing:4px;text-transform:uppercase;color:#FFD66B;margin-bottom:16px}}
.lh{{font-size:{int(A['lg']*0.92)}px;font-weight:900;line-height:1.0;letter-spacing:-1.8px;color:#fff;text-shadow:0 6px 36px rgba(0,0,0,.45);text-wrap:balance}}
.lh b{{color:#FFC21E}} .lh b.punch{{background:linear-gradient(90deg,#FFD54A,#FF8A3D);-webkit-background-clip:text;background-clip:text;color:transparent}}
.lsub{{margin-top:22px;font-size:{A['sub']-2}px;font-weight:500;line-height:1.4;color:rgba(255,255,255,.85);max-width:820px}}
.lsub b{{color:#fff;font-weight:700}}
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
<div class="stage">
 <div class="mesh"></div>
 {field_html}
 <div class="vign"></div><div class="grain"></div>
 {bigvec_html}
 <div class="pill">{kicker}</div>
 <div class="cardzone">{scene_divs}</div>
 <div class="lock"><span>APEX IT SOLUTIONS</span><span class="dot"></span><span>APEX MARKETINGS</span></div>
 <div class="pbarw"><div class="pbar"></div></div>
</div>
<script>
var W={W},H={H},TL={json.dumps(tl)};
function c01(x){{return x<0?0:x>1?1:x;}}
function lerp(a,b,u){{return a+(b-a)*u;}}
function eOut(u){{return 1-Math.pow(1-u,3);}}
function eIn(u){{return u*u;}}
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
   var lo=t-s.start,ln=s.end-s.start;
   if(lo<-0.3||lo>ln+0.05){{el.style.display='none';continue;}}
   el.style.display='block';
   var en=eOut(c01(lo/0.5)), ex=eIn(c01((lo-(ln-0.45))/0.45));
   el.style.opacity=(en*(1-ex)).toFixed(3);
   el.style.transform='translateY('+((1-en)*46 - ex*30).toFixed(1)+'px) scale('+(lerp(0.92,1,en)-ex*0.05).toFixed(3)+')';
   var cv=el.querySelectorAll('.cvec .cv');
   for(var ci=0;ci<cv.length;ci++){{var cu=eOut(c01((lo-0.2-ci*0.12)/0.5));
     cv[ci].style.opacity=cu.toFixed(3);
     cv[ci].style.transform='translateY('+((1-cu)*16).toFixed(1)+'px) scale('+lerp(0.6,1,cu).toFixed(3)+') rotate('+(Math.sin(t*0.8+ci)*4).toFixed(1)+'deg)';}}
   var pn=el.querySelectorAll('.punch');
   for(var m=0;m<pn.length;m++){{var at=parseFloat(pn[m].getAttribute('data-at')||'0.4');var pu=eOut(c01((lo-at)/0.5));
     pn[m].style.display='inline-block';pn[m].style.transform='scale('+lerp(0.7,1,pu).toFixed(3)+')';}}
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

def build_lush_slide_html(slide, idx, total, kicker, seed, W=1080, H=1350):
    """Static single carousel slide in the dark lush look. Reuses the SAME seeded palette +
    field as the video (so the carousel and video read as one set), frozen (no render(t)),
    with carousel slide copy + a slide-position indicator."""
    import build_today_video as V
    seed = int(seed or 0)
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
    GR = V.pack.GRAIN
    inner = _slide_inner(slide)
    style = f"""
*{{margin:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;font-family:'Segoe UI','Inter',Arial,sans-serif}}
.stage{{position:relative;width:{W}px;height:{H}px;background:#06070b;overflow:hidden}}
.mesh{{position:absolute;inset:-12%;background:{_bg(P)};filter:saturate(0.9) brightness(0.92)}}
.field{{position:absolute;inset:0;z-index:1;pointer-events:none}}
.field .fx{{position:absolute;opacity:.5}}
.field .fx[data-k="bub"]{{opacity:.32}}
.field .fx[data-k="star"]{{opacity:.6}}
.vign{{position:absolute;inset:0;z-index:2;background:radial-gradient(135% 105% at 50% 40%, transparent 52%, rgba(0,0,0,.74) 100%)}}
.grain{{position:absolute;inset:0;z-index:2;opacity:.05;mix-blend-mode:overlay;background:url('{GR}')}}
.bigvec-wrap{{position:absolute;inset:0;z-index:3;pointer-events:none}}
.bvec{{position:absolute;transform:translate(-50%,-50%);color:#FFD98A;filter:drop-shadow(0 0 14px rgba(255,200,90,.6));opacity:.42}}
.bvec .ic.accent{{color:#fff}}
.pill{{position:absolute;z-index:5;top:54px;left:56px;padding:13px 22px;border-radius:999px;font-size:16px;font-weight:800;letter-spacing:3px;text-transform:uppercase;color:#fff;background:rgba(255,255,255,.10);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,.22)}}
.cardzone{{position:absolute;z-index:4;left:56px;right:56px;top:300px;bottom:200px;display:flex;flex-direction:column;justify-content:center}}
.scene{{position:relative;padding:46px 48px;border-radius:34px;background:linear-gradient(160deg, rgba(255,255,255,.13), rgba(255,255,255,.04));backdrop-filter:blur(28px) saturate(1.3);-webkit-backdrop-filter:blur(28px) saturate(1.3);border:1px solid rgba(255,255,255,.22);box-shadow:0 40px 100px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.28)}}
.cvec{{display:flex;gap:14px;margin-bottom:18px}}
.cvec .cv{{display:inline-flex;align-items:center;justify-content:center;width:58px;height:58px;border-radius:15px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.2);color:#FFD98A;box-shadow:0 8px 22px rgba(0,0,0,.3)}}
.cvec .cv:nth-child(2){{color:#fff}}
.cvec .cv .ic{{width:34px;height:34px}}
.lstamp{{display:inline-flex;align-items:center;font-size:16px;font-weight:700;letter-spacing:.4px;color:rgba(255,255,255,.8);margin-bottom:14px}}
.lstamp .arr{{color:#FFC21E;font-weight:800;padding:0 8px}}
.ltag{{font-size:16px;font-weight:800;letter-spacing:4px;text-transform:uppercase;color:#FFD66B;margin-bottom:14px}}
.lh{{font-size:62px;font-weight:900;line-height:1.02;letter-spacing:-1.4px;color:#fff;text-shadow:0 6px 36px rgba(0,0,0,.45);text-wrap:balance}}
.lh b{{color:#FFC21E}}
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
    body = (f'<div class="stage"><div class="mesh"></div>{field_html}'
            f'<div class="vign"></div><div class="grain"></div>{bigvec_html}'
            f'<div class="pill">{apex_spec._amp(kicker)}</div>'
            f'<div class="cardzone"><div class="scene">{inner}</div></div>'
            f'<div class="dind">{dots}</div>'
            f'<div class="lock"><span>APEX IT SOLUTIONS</span><span class="dot"></span><span>APEX MARKETINGS</span></div>'
            f'</div>')
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{style}</style></head><body>{body}</body></html>"
