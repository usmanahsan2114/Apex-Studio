# -*- coding: utf-8 -*-
"""
apex_art.py — the shared, seeded ART-DIRECTOR for the Apex daily post system.

ONE seed (derived per post from id+date, or explicit spec["seed"]) selects a fully
curated "lookbook" and rolls seeded micro-jitter, producing a single `look` dict that
BOTH renderers consume:
  - build_today_pack.py  (image carousel) — world/layout/accents/type per day
  - build_today_video.py (reel)           — + transitions/motion/parallax/kinetic

Determinism is sacred: the video JS render(t) is a pure function of t + the baked TL
object. So ALL randomness happens HERE, once, in Python, and is baked into the HTML/CSS
and TL.style. Same seed -> identical look -> identical frames.

Design policy (user-chosen): amber stays the HERO accent on every post (the load-bearing
"punch" word is always amber); variety = background world, layout, motion, type, plus a
small seeded accent hue-nudge or a curated duotone in the *background only*. Theme rotates
mostly-dark, occasionally light.

Stdlib only. `build_today_pack` is imported lazily (avoids a circular import).
"""
import hashlib, json, os, random

ROOT = os.path.dirname(os.path.abspath(__file__))
MEMORY = os.path.join(ROOT, "art_memory.json")

def _pack():
    import build_today_pack as p   # lazy: pack may import us back inside its APEX_SPEC block
    return p

# ============================================================ color helpers
def _hex(h): h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def _hx(rgb): return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(v)))) for v in rgb)
def _rgba(h, a): r, g, b = _hex(h); return f"rgba({r},{g},{b},{a})"

def _rgb_hsl(rgb):
    r, g, b = [v/255 for v in rgb]; mx, mn = max(r, g, b), min(r, g, b); l = (mx+mn)/2
    if mx == mn: return 0.0, 0.0, l
    d = mx-mn; s = d/(2-mx-mn) if l > 0.5 else d/(mx+mn)
    if mx == r: h = (g-b)/d + (6 if g < b else 0)
    elif mx == g: h = (b-r)/d + 2
    else: h = (r-g)/d + 4
    return h/6, s, l
def _hsl_rgb(h, s, l):
    if s == 0: v = l*255; return (v, v, v)
    def hue(p, q, t):
        t %= 1
        if t < 1/6: return p+(q-p)*6*t
        if t < 1/2: return q
        if t < 2/3: return p+(q-p)*(2/3-t)*6
        return p
    q = l*(1+s) if l < 0.5 else l+s-l*s; p = 2*l-q
    return tuple(255*hue(p, q, h+o) for o in (1/3, 0, -1/3))
def _shift_hue(h, deg):
    hh, s, l = _rgb_hsl(_hex(h)); return _hx(_hsl_rgb((hh + deg/360.0) % 1.0, s, l))

# Curated SECOND colours for duotone looks (deep, used only in backgrounds — never on text).
DUO = {
    "indigo": {"dark": "#5663D6", "light": "#3C46B4"},
    "teal":   {"dark": "#2BB8AE", "light": "#138F87"},
    "violet": {"dark": "#8A6BE0", "light": "#6A4ECB"},
    "rose":   {"dark": "#E0738F", "light": "#C24E6C"},
    "azure":  {"dark": "#3FA9F5", "light": "#1E78C8"},
}

# ============================================================ v2 art dimensions
FONTPAIRS = {
    "system": dict(display="Segoe UI", body="Segoe UI", weight=800, case="none", italic_punch=False, track=0),
    "condensed_ops": dict(display="Archivo", body="Inter", weight=900, case="none", italic_punch=False, track=-0.4),
    "technical_saas": dict(display="Sora", body="Space Grotesk", weight=800, case="none", italic_punch=False, track=0.0),
    "editorial_serif": dict(display="Fraunces", body="Newsreader", weight=850, case="none", italic_punch=True, track=0.2),
    "extended_signal": dict(display="Syne", body="Manrope", weight=800, case="none", italic_punch=False, track=0.6),
    "expressive_growth": dict(display="Bricolage Grotesque", body="Geist", weight=850, case="none", italic_punch=False, track=-0.2),
}

LAYOUTS = {
    "centered": dict(label="Centered"),
    "left_editorial": dict(label="Left editorial"),
    "split": dict(label="Split system"),
    "asymmetric_hero": dict(label="Asymmetric hero"),
    "grid": dict(label="Grid lab"),
    "full_bleed_type": dict(label="Full bleed type"),
}

TONES = {
    "amber_signature": dict(mode="signature"),
    "duotone_indigo": dict(mode="duotone", duo="indigo"),
    "duotone_teal": dict(mode="duotone", duo="teal"),
    "duotone_violet": dict(mode="duotone", duo="violet"),
    "duotone_rose": dict(mode="duotone", duo="rose"),
    "duotone_azure": dict(mode="duotone", duo="azure"),
    "mono_warm": dict(mode="mono", dark_base="#14120E", dark_grad="linear-gradient(168deg,#1A1711,#14120E 48%,#10100D)"),
    "mono_cool": dict(mode="mono", dark_base="#0D1215", dark_grad="linear-gradient(168deg,#141B20,#10161A 48%,#0D1115)"),
    "editorial_cream": dict(mode="paper", base="#F7F3EA", bg="linear-gradient(168deg,#FFFDF7,#F5F0E7 48%,#EEE7DB)"),
}

D3S = {
    "none": dict(label="None"),
    "extruded_type": dict(label="Extruded type"),
    "prism_rotate": dict(label="Prism rotate"),
    "card_stack_3d": dict(label="Card stack 3D"),
    "depth_parallax": dict(label="Depth parallax"),
    "coin_tower": dict(label="Coin tower"),
}

LOOK_V2 = {
    "noir_editorial": dict(fonts=["editorial_serif", "technical_saas", "system"], layouts=["centered", "left_editorial", "asymmetric_hero"], tones=["amber_signature", "mono_warm", "duotone_indigo"], d3=["depth_parallax", "card_stack_3d", "none"]),
    "blueprint": dict(fonts=["technical_saas", "condensed_ops"], layouts=["grid", "split", "centered"], tones=["amber_signature", "duotone_teal", "mono_cool"], d3=["depth_parallax", "card_stack_3d"]),
    "swiss_grid": dict(fonts=["technical_saas", "editorial_serif"], layouts=["left_editorial", "grid", "split"], tones=["amber_signature", "editorial_cream"], d3=["none", "card_stack_3d"]),
    "spotlight": dict(fonts=["condensed_ops", "expressive_growth"], layouts=["asymmetric_hero", "full_bleed_type", "centered"], tones=["amber_signature", "duotone_rose"], d3=["extruded_type", "prism_rotate"]),
    "aurora_mesh": dict(fonts=["extended_signal", "expressive_growth"], layouts=["asymmetric_hero", "split"], tones=["duotone_teal", "duotone_azure", "duotone_violet"], d3=["prism_rotate", "depth_parallax"]),
    "data_room": dict(fonts=["technical_saas", "condensed_ops"], layouts=["grid", "split"], tones=["amber_signature", "mono_cool", "duotone_azure"], d3=["card_stack_3d", "depth_parallax"]),
    "kinetic_bold": dict(fonts=["condensed_ops", "extended_signal"], layouts=["full_bleed_type", "asymmetric_hero"], tones=["amber_signature", "duotone_rose"], d3=["extruded_type", "prism_rotate"]),
    "magazine": dict(fonts=["editorial_serif", "expressive_growth"], layouts=["left_editorial", "split"], tones=["editorial_cream", "amber_signature"], d3=["none", "card_stack_3d"]),
    "minimal_mono": dict(fonts=["system", "technical_saas"], layouts=["centered", "left_editorial"], tones=["amber_signature", "mono_warm", "mono_cool"], d3=["none", "depth_parallax"]),
    "duotone": dict(fonts=["extended_signal", "expressive_growth"], layouts=["split", "asymmetric_hero"], tones=["duotone_indigo", "duotone_violet", "duotone_rose"], d3=["prism_rotate", "depth_parallax"]),
    "signal_hud": dict(fonts=["technical_saas", "condensed_ops"], layouts=["grid", "split", "asymmetric_hero"], tones=["amber_signature", "duotone_teal", "mono_cool"], d3=["card_stack_3d", "depth_parallax"]),
    "graphite": dict(fonts=["condensed_ops", "technical_saas"], layouts=["centered", "split", "asymmetric_hero"], tones=["amber_signature", "mono_warm"], d3=["extruded_type", "card_stack_3d"]),
}

# ============================================================ palette grading
def palette_for(look, theme):
    """Resolve the palette dict for a theme (superset of pack.PALETTES[theme]:
    existing keys preserved so all current CSS `{P['..']}` interpolations still work)."""
    P = dict(_pack().PALETTES[theme]); g = look.get("grade", {}); mode = g.get("accent", "hero")
    if mode == "shift":
        am = _shift_hue(P["amber"], g.get("shift_deg", 0.0)); P["amber"] = am
        r, gr, b = _hex(am)
        P["glow"] = f"radial-gradient(760px 620px at 50% 38%, rgba({r},{gr},{b},.10), transparent 62%)"
        P["qbar"] = f"linear-gradient(90deg,{P['neutral']},{am})"
        P["lane_glow"] = (f"0 0 16px rgba({r},{gr},{b},.5)") if theme == "dark" else "none"
    P.setdefault("accent2", P["amber"])
    if mode == "duotone":
        a2 = DUO.get(g.get("duo", "indigo"), DUO["indigo"])[theme]; P["accent2"] = a2
        r2, g2, b2 = _hex(a2); ar, ag, ab = _hex(P["amber"])
        om = ".12" if theme == "dark" else ".06"; ov = ".09" if theme == "dark" else ".05"
        P["mesh"] = (f"radial-gradient(720px 600px at 20% 22%, rgba({ar},{ag},{ab},{om}), transparent 60%),"
                     f"radial-gradient(760px 640px at 84% 82%, rgba({r2},{g2},{b2},{ov}), transparent 62%)")
        P["glow"] = f"radial-gradient(820px 660px at 50% 36%, rgba({ar},{ag},{ab},.11), transparent 64%)"
    tone_name = g.get("tone", "amber_signature")
    tone = TONES.get(tone_name, TONES["amber_signature"])
    if tone.get("mode") == "duotone":
        a2 = DUO.get(tone.get("duo", "indigo"), DUO["indigo"])[theme]
        P["accent2"] = a2
        r2, g2, b2 = _hex(a2); ar, ag, ab = _hex(P["amber"])
        if theme == "dark":
            P["mesh"] = (f"radial-gradient(720px 600px at 16% 20%, rgba({ar},{ag},{ab},.10), transparent 60%),"
                         f"radial-gradient(760px 640px at 88% 82%, rgba({r2},{g2},{b2},.13), transparent 62%)")
            P["glow"] = f"radial-gradient(860px 690px at 48% 36%, rgba({r2},{g2},{b2},.10), transparent 64%)"
    elif tone.get("mode") == "mono" and theme == "dark":
        P["base"] = tone["dark_base"]; P["bg_grad"] = tone["dark_grad"]
        P["mesh"] = "radial-gradient(720px 580px at 24% 28%, rgba(255,255,255,.055), transparent 62%)"
    elif tone.get("mode") == "paper" and theme == "light":
        P["base"] = tone["base"]; P["bg_grad"] = tone["bg"]
        P["text_primary"] = "#15130F"; P["text_secondary"] = "#50483D"; P["text_tertiary"] = "#72695B"
        P["hairline"] = "#DDD2C2"; P["dot"] = "rgba(22,18,14,.045)"
    return P

# ============================================================ background LAYER emitters
# Each: layer(params, P, theme, W, H) -> (css_text, html_text). Concatenated by world_css/html.
# The "classic" layers reproduce the CURRENT stack faithfully (zero regression for the base look).
def _l_grain(p, P, th, W, H):
    o = p.get("opacity", P["grain"])
    css = f".grain{{position:absolute;inset:0;background:url('{_pack().GRAIN}');opacity:{o};mix-blend-mode:overlay;pointer-events:none;z-index:0}}"
    return css, '<div class="grain"></div>'
def _l_dots(p, P, th, W, H):
    sz = p.get("size", 33)
    css = (f".dots{{position:absolute;inset:0;background-image:radial-gradient(circle,{P['dot']} 1.2px,transparent 1.4px);"
           f"background-size:{sz}px {sz}px;pointer-events:none;z-index:0}}")
    return css, '<div class="dots"></div>'
def _l_glow(p, P, th, W, H):
    css = f".glow{{position:absolute;inset:0;background:{P['glow']};pointer-events:none;z-index:0}}"
    return css, '<div class="glow"></div>'
def _l_mesh(p, P, th, W, H):
    css = f".mesh{{position:absolute;inset:0;background:{P['mesh']};opacity:{_pack().bgop(p.get('opacity',1.0))};pointer-events:none;z-index:0}}"
    return css, '<div class="mesh"></div>'
def _l_vignette(p, P, th, W, H):
    css = f".vignette{{position:absolute;inset:0;background:{P['vignette']};opacity:{_pack().bgop(p.get('opacity',1.0))};pointer-events:none;z-index:1}}"
    return css, '<div class="vignette"></div>'
def _l_rings(p, P, th, W, H):
    css = ".rings{position:absolute;left:50%;top:46%;transform:translate(-50%,-50%);pointer-events:none;z-index:0}"
    return css, _pack().rings_svg(P)
def _l_spotlight(p, P, th, W, H):
    ar, ag, ab = _hex(P["amber"]); i = p.get("intensity", 0.14); x = p.get("x", 50); y = p.get("y", 30)
    dk = ".46" if th == "dark" else ".14"
    css = (f".spot{{position:absolute;inset:0;pointer-events:none;z-index:1;"
           f"background:radial-gradient(680px 720px at {x}% {y}%, rgba({ar},{ag},{ab},{i}), transparent 60%),"
           f"radial-gradient(140% 120% at 50% 42%, transparent 38%, rgba(0,0,0,{dk}) 100%)}}")
    return css, '<div class="spot"></div>'
def _l_beam(p, P, th, W, H):
    ar, ag, ab = _hex(P["amber"]); i = p.get("intensity", 0.13); ang = p.get("angle", 18); x = p.get("x", 60)
    css = (f".beam{{position:absolute;left:{x}%;top:-30%;width:60%;height:170%;pointer-events:none;z-index:1;"
           f"transform-origin:top center;transform:translateX(-50%) rotate({ang}deg);"
           f"background:linear-gradient(90deg,transparent,rgba({ar},{ag},{ab},{i}) 50%,transparent);filter:blur(28px)}}")
    return css, '<div class="beam"></div>'
def _l_blob(p, P, th, W, H):
    ar, ag, ab = _hex(P["amber"]); r2, g2, b2 = _hex(P.get("accent2", P["amber"]))
    blobs = p.get("blobs", [{"x": 24, "y": 30, "c": "amber"}, {"x": 78, "y": 72, "c": "accent2"}])
    html = []
    for k, b in enumerate(blobs):
        rr, gg, bb = (ar, ag, ab) if b.get("c") == "amber" else (r2, g2, b2)
        a = ".10" if th == "dark" else ".06"
        html.append(f'<div class="blob blob{k}" style="left:{b["x"]}%;top:{b["y"]}%;'
                     f'background:radial-gradient(circle,rgba({rr},{gg},{bb},{a}),transparent 70%)"></div>')
    css = ".blob{position:absolute;width:520px;height:520px;transform:translate(-50%,-50%);border-radius:50%;pointer-events:none;z-index:0;filter:blur(36px)}"
    return css, "".join(html)
def _l_scan(p, P, th, W, H):
    o = p.get("opacity", 0.05 if th == "dark" else 0.03); gap = p.get("gap", 4)
    line = _rgba(P["text_primary"], o)
    css = (f".scan{{position:absolute;inset:0;pointer-events:none;z-index:1;"
           f"background:repeating-linear-gradient(0deg,transparent 0,transparent {gap-1}px,{line} {gap-1}px,{line} {gap}px)}}")
    return css, '<div class="scan"></div>'
def _l_grid(p, P, th, W, H):
    o = p.get("opacity", 0.06 if th == "dark" else 0.05); sz = p.get("size", 72)
    ln = _rgba(P["text_primary"], o)
    css = (f".grid{{position:absolute;inset:-2px;pointer-events:none;z-index:0;"
           f"background-image:linear-gradient({ln} 1px,transparent 1px),linear-gradient(90deg,{ln} 1px,transparent 1px);"
           f"background-size:{sz}px {sz}px}}")
    return css, '<div class="grid"></div>'
def _l_hairgrid(p, P, th, W, H):
    o = p.get("opacity", 0.04 if th == "dark" else 0.045); sz = p.get("size", 120)
    ln = _rgba(P["text_primary"], o)
    css = (f".hairgrid{{position:absolute;inset:0;pointer-events:none;z-index:0;"
           f"background-image:linear-gradient(90deg,{ln} 1px,transparent 1px);background-size:{sz}px {sz}px}}")
    return css, '<div class="hairgrid"></div>'
def _l_sweep(p, P, th, W, H):
    ar, ag, ab = _hex(P["amber"]); i = p.get("intensity", 0.07)
    css = (f".sweepbg{{position:absolute;inset:-20%;pointer-events:none;z-index:0;transform:rotate(-12deg);"
           f"background:linear-gradient(100deg,transparent 30%,rgba({ar},{ag},{ab},{i}) 50%,transparent 70%)}}")
    return css, '<div class="sweepbg"></div>'
def _l_orbs(p, P, th, W, H):
    n = p.get("count", 5); ar, ag, ab = _hex(P["amber"])
    css = (f".orb{{position:absolute;left:50%;top:42%;width:9px;height:9px;border-radius:50%;"
           f"background:rgba({ar},{ag},{ab},.16);filter:blur(.5px);pointer-events:none;z-index:1}}")
    return css, "".join('<div class="orb particle"></div>' for _ in range(n))
def _l_particles(p, P, th, W, H):
    n = p.get("count", 6); ar, ag, ab = _hex(P["amber"])
    css = (f".particle{{position:absolute;left:50%;top:42%;width:7px;height:7px;border-radius:50%;"
           f"background:rgba({ar},{ag},{ab},.16);filter:blur(.5px);pointer-events:none;z-index:1}}")
    return css, "".join('<div class="particle"></div>' for _ in range(n))

LAYERS = dict(grain=_l_grain, dots=_l_dots, glow=_l_glow, mesh=_l_mesh, vignette=_l_vignette,
              rings=_l_rings, spotlight=_l_spotlight, beam=_l_beam, blob=_l_blob, scan=_l_scan,
              grid=_l_grid, hairgrid=_l_hairgrid, sweep=_l_sweep, orbs=_l_orbs, particles=_l_particles)

# ============================================================ accent (decoration) emitters
def _a_brackets(p, P, th, W, H, idx):
    ins = p.get("inset", 50)
    css = (f".brwrap{{position:absolute;inset:0;z-index:2;pointer-events:none}}"
           f".br{{position:absolute;width:33px;height:33px;border:1.5px solid {P['bracket']}}}"
           f".br.tl{{top:{ins}px;left:{ins}px;border-right:0;border-bottom:0}}.br.tr{{top:{ins}px;right:{ins}px;border-left:0;border-bottom:0}}"
           f".br.bl{{bottom:{ins}px;left:{ins}px;border-right:0;border-top:0}}.br.rb{{bottom:{ins}px;right:{ins}px;border-left:0;border-top:0}}")
    return css, '<div class="brwrap"><div class="br tl"></div><div class="br tr"></div><div class="br bl"></div><div class="br rb"></div></div>'
def _a_guides(p, P, th, W, H, idx):
    css = ".guides{position:absolute;inset:0;z-index:2;pointer-events:none}"
    return css, f'<div class="guides">{_pack().guides(P)}</div>'
def _a_ghost(p, P, th, W, H, idx):
    css = ".ghostwrap{position:absolute;inset:0;z-index:0;pointer-events:none;overflow:hidden}"
    return css, f'<div class="ghostwrap">{_pack().ghost_glyph(P, idx or 1)}</div>'
def _a_ticks(p, P, th, W, H, idx):
    tk = P["tick"]; L = []
    for x in range(120, W-90, 84):
        L.append(f'<line x1="{x}" y1="34" x2="{x}" y2="44" stroke="{tk}" stroke-width="1"/>')
        L.append(f'<line x1="{x}" y1="{H-34}" x2="{x}" y2="{H-44}" stroke="{tk}" stroke-width="1"/>')
    css = ".ticks{position:absolute;inset:0;z-index:2;pointer-events:none}"
    return css, f'<svg class="ticks" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(L)}</svg>'
def _a_hud(p, P, th, W, H, idx):
    g = P["bracket"]; m = 50; s = 26
    seg = lambda x1, y1, x2, y2: f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{g}" stroke-width="1.5"/>'
    parts = (seg(m, m+s, m, m) + seg(m, m, m+s, m) + seg(W-m-s, m, W-m, m) + seg(W-m, m, W-m, m+s)
             + seg(m, H-m-s, m, H-m) + seg(m, H-m, m+s, H-m) + seg(W-m-s, H-m, W-m, H-m) + seg(W-m, H-m, W-m, H-m-s))
    dotc = _rgba(P["amber"], .6)
    parts += f'<circle cx="{m+6}" cy="{m+6}" r="2" fill="{dotc}"/><circle cx="{W-m-6}" cy="{H-m-6}" r="2" fill="{dotc}"/>'
    css = ".hud{position:absolute;inset:0;z-index:2;pointer-events:none}"
    return css, f'<svg class="hud" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{parts}</svg>'
def _a_indexnum(p, P, th, W, H, idx):
    n = (idx or 1); col = _rgba(P["amber"], .12 if th == "dark" else .14)
    css = ".idxnum{position:absolute;top:%dpx;right:64px;z-index:1;pointer-events:none}" % (int(H*0.12))
    html = (f'<div class="idxnum" style="font:800 220px \'Segoe UI\',Arial;letter-spacing:-10px;'
            f'color:{col};line-height:.8">{n:02d}</div>')
    return css, html
def _a_rule(p, P, th, W, H, idx):
    ln = P["hairline"]
    css = ".rulewrap{position:absolute;inset:0;z-index:1;pointer-events:none}"
    html = (f'<div class="rulewrap"><div style="position:absolute;left:64px;right:64px;top:{int(H*0.26)}px;height:1px;background:{ln}"></div>'
            f'<div style="position:absolute;left:64px;right:64px;bottom:{int(H*0.22)}px;height:1px;background:{ln}"></div></div>')
    return css, html
def _a_radar(p, P, th, W, H, idx):
    cx, cy, r = W-110, 150, 64; ar = P["amber"]; rng_c = P["ring"]
    css = ".radar{position:absolute;inset:0;z-index:1;pointer-events:none;opacity:.7}"
    html = (f'<svg class="radar" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{rng_c}" stroke-width="1"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r*0.6:.0f}" fill="none" stroke="{rng_c}" stroke-width="1"/>'
            f'<line id="radln" x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy-r}" stroke="{ar}" stroke-width="1.6" stroke-linecap="round"/>'
            f'<circle cx="{cx}" cy="{cy}" r="2.5" fill="{ar}"/></svg>')
    return css, html

ACCENTS = dict(brackets=_a_brackets, guides=_a_guides, ghost=_a_ghost, ticks=_a_ticks,
               hud=_a_hud, indexnum=_a_indexnum, rule=_a_rule, radar=_a_radar)

# ============================================================ public emitters
def world_css(look, theme, W, H):
    P = palette_for(look, theme); out = []
    for layer in look.get("world", []):
        f = LAYERS.get(layer.get("id"))
        if f: out.append(f(layer, P, theme, W, H)[0])
    for acc in look.get("accents", []):
        f = ACCENTS.get(acc)
        if f: out.append(f({}, P, theme, W, H, look.get("_idx"))[0])
    return "\n".join(out)

def world_html(look, theme, W, H, idx=None):
    P = palette_for(look, theme); out = []
    for layer in look.get("world", []):
        f = LAYERS.get(layer.get("id"))
        if f: out.append(f(layer, P, theme, W, H)[1])
    for acc in look.get("accents", []):
        f = ACCENTS.get(acc)
        if f: out.append(f({}, P, theme, W, H, idx)[1])
    return "\n".join(out)

def _font_stack(name):
    if not name or name == "Segoe UI":
        return "'Segoe UI','Inter',Arial,sans-serif"
    return "'" + name.replace("'", "") + "','Segoe UI','Inter',Arial,sans-serif"

def _font_entries():
    path = os.path.join(ROOT, "assets", "fonts", "manifest.json")
    try:
        with open(path, encoding="utf-8") as f:
            return (json.load(f) or {}).get("entries", [])
    except Exception:
        return []

def fontface_css(look):
    fonts = (look or {}).get("fonts", {})
    wanted = {fonts.get("display"), fonts.get("body")} - {None, "", "Segoe UI"}
    if not wanted:
        return ""
    out = []
    for ent in _font_entries():
        fam = ent.get("family")
        if fam not in wanted:
            continue
        fp = os.path.join(ROOT, "assets", "fonts", ent.get("file", ""))
        try:
            import base64
            data = base64.b64encode(open(fp, "rb").read()).decode("ascii")
        except Exception:
            continue
        fmt = ent.get("format", "woff2")
        weight = ent.get("weight", "100 900")
        style = ent.get("style", "normal")
        stretch = ent.get("stretch", "normal")
        ur = ent.get("unicode_range") or ""
        ur_css = f"unicode-range:{ur};" if ur else ""
        mime = "font/ttf" if fmt == "truetype" else "font/woff2"
        out.append(
            "@font-face{font-family:'%s';src:url(data:%s;base64,%s) format('%s');"
            "font-weight:%s;font-style:%s;font-stretch:%s;font-display:block;%s}" %
            (fam.replace("'", ""), mime, data, fmt, weight, style, stretch, ur_css)
        )
    return "\n".join(out)

def type_css(look, sel_xl=".hxl", sel_lg=".hlg"):
    t = look.get("type", {}); w = t.get("weight", 800)
    tr_xl = t.get("track_xl", -2.0); tr_lg = t.get("track_lg", -1.2); sc = t.get("scale", 1.0)
    al = look.get("layout", {}).get("align", "center")
    fnt = look.get("fonts", {}) or {}
    display_stack = _font_stack(fnt.get("display", "Segoe UI"))
    body_stack = _font_stack(fnt.get("body", "Segoe UI"))
    transform = "uppercase" if fnt.get("case") == "upper" else "none"
    italic = "font-style:italic;" if fnt.get("italic_punch") else ""
    css = (f"body,.canvas{{font-family:{body_stack}}} "
           f"{sel_xl},{sel_lg},.kicker,.tag,.bname,.lab{{font-family:{display_stack};text-transform:{transform}}} "
           f"{sel_xl}{{font-weight:{w};letter-spacing:{tr_xl}px}} {sel_lg}{{font-weight:{w};letter-spacing:{tr_lg}px}} "
           f".motif text{{font-family:{display_stack}}} .punch{{{italic}}}")
    if abs(sc-1.0) > 0.001:
        css += f" {sel_xl},{sel_lg}{{zoom:{sc:.3f}}}"
    if al == "left":
        css += (f" .scene{{align-items:flex-start!important;text-align:left!important}}"
                f" .body{{align-items:flex-start!important;text-align:left!important}}"
                f" {sel_xl},{sel_lg},.sub,.ctabox{{text-align:left!important}} .sub,.ctabox{{margin-left:0!important}}")
    return css

_HAL = {"left": ("flex-start", "left"), "center": ("center", "center"), "right": ("flex-end", "right")}
_VAL = {"top": "flex-start", "center": "center", "bottom": "flex-end"}

def _per_scene_css(look):
    """Per-scene placement overrides (video). id+class specificity beats the template's `.scene` rules."""
    ps = ((look or {}).get("layout", {}) or {}).get("per_scene") or []
    out = []
    for i, s in enumerate(ps):
        ha, ta = _HAL.get(s.get("h", "center"), _HAL["center"]); va = _VAL.get(s.get("v", "center"), "center")
        ml = "0" if ta == "left" else "auto"; mr = "0" if ta == "right" else "auto"
        out.append(f".scene#s{i+1}{{align-items:{ha}!important;justify-content:{va}!important;text-align:{ta}!important}}"
                   f".scene#s{i+1} .sub,.scene#s{i+1} .ctabox{{margin-left:{ml}!important;margin-right:{mr}!important;text-align:{ta}!important}}")
    return "".join(out)

def layout_css(look, W, H, kind="video"):
    tmpl = ((look or {}).get("layout", {}) or {}).get("template", "centered")
    per = _per_scene_css(look) if kind == "video" else ""
    if tmpl == "centered":
        return per
    if kind == "carousel":
        if tmpl == "left_editorial":
            return ".head{align-self:flex-start!important;align-items:flex-start!important}.body{align-items:flex-start!important;text-align:left!important;padding-left:56px;padding-right:120px}.sub,.ctabox{margin-left:0!important}.foot{align-items:flex-start!important}.lockup{justify-content:flex-start!important}"
        if tmpl == "split":
            return ".body{align-items:flex-start!important;text-align:left!important;padding-left:44px}.hxl,.hlg{max-width:720px}.sub{margin-left:0!important;max-width:660px}.split{margin-left:0!important}.stamp{align-self:flex-start}"
        if tmpl == "asymmetric_hero":
            return ".body{align-items:flex-start!important;text-align:left!important;padding-left:32px;padding-right:280px}.hxl,.hlg{max-width:710px}.sub,.ctabox{margin-left:0!important}.rings{left:68%!important}.ghostwrap,.idxnum{opacity:.75}"
        if tmpl == "grid":
            return ".canvas{padding-left:88px!important;padding-right:88px!important}.body{align-items:flex-start!important;text-align:left!important}.hxl,.hlg,.sub,.ctabox{text-align:left!important}.sub,.ctabox{margin-left:0!important}.stamp{align-self:flex-start}.split{margin-left:0!important}"
        if tmpl == "full_bleed_type":
            return ".body{width:110%!important}.hxl{font-size:96px!important;letter-spacing:-3px!important}.hlg{font-size:68px!important}.sub{max-width:900px}.rings{transform:translate(-50%,-50%) scale(1.2)!important}"
        return ""
    # video layouts (template base + per-scene placement overrides)
    if tmpl == "left_editorial":
        return ".head{left:92px!important;right:auto!important;align-items:flex-start!important}.stage{left:96px!important;right:190px!important}.scene{align-items:flex-start!important;text-align:left!important}.sub,.ctabox{margin-left:0!important;text-align:left!important}.foot{align-items:flex-start!important;left:96px!important;right:96px!important}.lockup{justify-content:flex-start!important}.motif{left:74%!important}" + per
    if tmpl == "split":
        return ".stage{left:82px!important;right:82px!important}.scene{align-items:flex-start!important;text-align:left!important}.scene .hxl,.scene .hlg{max-width:720px}.sub,.ctabox{margin-left:0!important;text-align:left!important}.motif{left:73%!important;top:31%!important}" + per
    if tmpl == "asymmetric_hero":
        return ".stage{left:82px!important;right:360px!important}.scene{align-items:flex-start!important;text-align:left!important}.sub,.ctabox{text-align:left!important;margin-left:0!important}.motif{left:75%!important;top:36%!important}.motif svg{filter:drop-shadow(0 28px 60px rgba(0,0,0,.32))}" + per
    if tmpl == "grid":
        return ".stage{left:92px!important;right:92px!important;top:30%!important}.scene{align-items:flex-start!important;text-align:left!important}.sub,.ctabox{text-align:left!important;margin-left:0!important}.motif{left:72%!important}.head{align-items:flex-start!important;left:92px!important;right:auto!important}" + per
    if tmpl == "full_bleed_type":
        return ".stage{left:28px!important;right:28px!important;top:28%!important;height:50%!important}.hxl{font-size:136px!important;letter-spacing:-4px!important}.hlg{font-size:96px!important}.sub{max-width:900px}.motif{opacity:.45;left:50%!important;top:42%!important}" + per
    return per

def d3_css(look, theme="dark"):
    mode = ((look or {}).get("d3", {}) or {}).get("mode", "none")
    if mode == "none":
        return ""
    ar, ag, ab = _hex(palette_for(look, theme)["amber"])
    # z-index:2 -> sits ABOVE the background world (0-1) but BELOW the text stage (3),
    # so the 3D reads boldly without hurting headline legibility. perspective tuned (~840) for real depth.
    base = (
        ".canvas{perspective:840px;perspective-origin:50% 40%}"
        ".stage,.scene{transform-style:preserve-3d}"
        ".d3-world{position:absolute;inset:0;z-index:2;pointer-events:none;transform-style:preserve-3d}"
        ".d3-prism,.d3-card,.d3-ring{position:absolute;transform-style:preserve-3d;will-change:transform,opacity}"
        ".d3-prism{right:14%;top:20%;width:220px;height:220px;opacity:.95}"
        f".d3-face{{position:absolute;inset:0;border:1.6px solid rgba({ar},{ag},{ab},.6);"
        f"background:linear-gradient(135deg,rgba({ar},{ag},{ab},.22),rgba(255,255,255,.05));"
        f"box-shadow:inset 0 0 55px rgba({ar},{ag},{ab},.16),0 30px 80px rgba(0,0,0,.42)}}"
        ".d3-face.f0{transform:translateZ(110px)}.d3-face.f1{transform:rotateY(90deg) translateZ(110px)}"
        ".d3-face.f2{transform:rotateY(180deg) translateZ(110px)}.d3-face.f3{transform:rotateY(-90deg) translateZ(110px)}"
        ".d3-face.f4{transform:rotateX(90deg) translateZ(110px)}.d3-face.f5{transform:rotateX(-90deg) translateZ(110px)}"
        f".d3-stack .d3-card{{right:8%;top:24%;width:300px;height:188px;border:1.6px solid rgba({ar},{ag},{ab},.5);border-radius:18px;"
        f"background:linear-gradient(135deg,rgba({ar},{ag},{ab},.18),rgba(255,255,255,.055));"
        f"box-shadow:0 38px 95px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.10)}}"
        # coin_tower: stacked extruded coin discs
        f".d3-tower .d3-ring{{right:16%;top:34%;width:210px;height:58px;border-radius:50%;border:2px solid rgba({ar},{ag},{ab},.6);"
        f"background:radial-gradient(ellipse at 50% 35%,rgba({ar},{ag},{ab},.28),rgba(0,0,0,.22));"
        f"box-shadow:0 16px 34px rgba(0,0,0,.42)}}"
    )
    if mode == "extruded_type":
        return base + (f".hxl,.hlg{{text-shadow:"
            f"1px 1px 0 rgba({ar},{ag},{ab},.95),2px 3px 0 rgba({ar},{ag},{ab},.55),"
            f"4px 6px 0 rgba(0,0,0,.55),8px 11px 0 rgba(0,0,0,.42),13px 18px 0 rgba(0,0,0,.32),"
            f"20px 28px 52px rgba(0,0,0,.6)}}")
    if mode == "depth_parallax":
        return base + ".mesh,.rings,.glow,.motif{transform-style:preserve-3d;will-change:transform}"
    return base

def d3_html(look, theme="dark"):
    mode = ((look or {}).get("d3", {}) or {}).get("mode", "none")
    if mode == "prism_rotate":
        faces = "".join(f'<div class="d3-face f{i}"></div>' for i in range(6))
        return f'<div class="d3-world"><div class="d3-prism" id="d3prism">{faces}</div></div>'
    if mode == "card_stack_3d":
        cards = "".join(f'<div class="d3-card c{i}"></div>' for i in range(4))
        return f'<div class="d3-world d3-stack" id="d3stack">{cards}</div>'
    if mode == "coin_tower":
        rings = "".join(f'<div class="d3-ring r{i}"></div>' for i in range(6))
        return f'<div class="d3-world d3-tower" id="d3tower">{rings}</div>'
    return ""

# ============================================================ seeded selection
def derive_seed(spec):
    # Pinned seed in the spec -> reproducible. Else APEX_SEED env -> one shared seed across the
    # carousel + video processes of a single generation (cohesion). Else id|date hash (stable per day).
    # Per-generation randomness comes from apex_concept.generate() injecting a fresh "seed" into the spec.
    if isinstance(spec, dict) and spec.get("seed") is not None:
        try: return int(spec["seed"]) & 0x7FFFFFFF
        except Exception: pass
    env_seed = os.environ.get("APEX_SEED")
    if env_seed:
        try: return int(env_seed) & 0x7FFFFFFF
        except Exception: pass
    sid = (spec.get("id") if isinstance(spec, dict) else None) or "day"
    date = (spec.get("date") if isinstance(spec, dict) else None) or ""
    return int(hashlib.sha256(f"{sid}|{date}".encode()).hexdigest()[:8], 16)

def _rng_range(rng, v):
    return rng.uniform(v[0], v[1]) if isinstance(v, (list, tuple)) else v

def _art_hint(spec, key):
    if not isinstance(spec, dict):
        return None
    v = spec.get("video") or {}
    art = v.get("art") if isinstance(v, dict) else {}
    if isinstance(art, dict) and art.get(key) is not None:
        return art.get(key)
    # Support both user-friendly and shorter field names.
    aliases = {
        "font_pairing": ["font_pairing", "font_pack"],
        "layout": ["layout", "scene_pack"],
        "tone": ["tone"],
        "d3": ["d3", "hero_3d"],
    }.get(key, [key])
    for k in aliases:
        if spec.get(k) is not None:
            return spec.get(k)
        if isinstance(v, dict) and v.get(k) is not None:
            return v.get(k)
    return None

def _roll_v2(rng, lbn, key, registry, fallback):
    field = "d3" if key == "d3" else key + "s"
    vals = LOOK_V2.get(lbn, {}).get(field) or [fallback]
    vals = [v for v in vals if v in registry] or [fallback]
    return rng.choice(vals)

# Lookbook catalog — each is a frozen bundle of CONSTRAINED ranges. The art-director only
# ever picks a whole lookbook; jitter only moves within its declared ranges (anti-ugliness).
LOOKBOOKS = {
 "noir_editorial": dict(weight=12, themes=["dark","dark","light"], accent="hero",
    world=["grain","dots","glow","mesh","vignette","rings"], accents=["brackets","guides","ghost"],
    align="center", scale=(0.98,1.02), track_xl=(-2.2,-1.8), emphasis="punch",
    transitions=["fade_clip","blur_dissolve"], easing="outCubic", punch_ease="outBack", motif_ease="outCubic",
    parallax=(0.4,0.5), motion="calm", particles=(5,7)),
 "blueprint": dict(weight=9, themes=["dark","dark","light"], accent="hero",
    world=["grid","dots","glow","vignette"], accents=["brackets","ticks","hud"],
    align="center", scale=(0.97,1.0), track_xl=(-1.4,-1.0), emphasis="word_stagger",
    transitions=["mask_wipe_v","push_slide"], easing="outExpo", punch_ease="outExpo", motif_ease="outExpo",
    parallax=(0.5,0.65), motion="precise", particles=(0,0)),
 "swiss_grid": dict(weight=8, themes=["light","light","dark"], accent="hero",
    world=["hairgrid","dots","glow"], accents=["rule","indexnum"],
    align="left", scale=(1.02,1.06), track_xl=(-1.8,-1.4), emphasis="block_mask",
    transitions=["push_slide","card_stack"], easing="outExpo", punch_ease="outBack", motif_ease="outExpo",
    parallax=(0.25,0.35), motion="snappy", particles=(0,0)),
 "spotlight": dict(weight=9, themes=["dark","dark","dark"], accent="hero",
    world=["spotlight","grain","blob"], accents=["brackets"],
    align="center", scale=(1.0,1.04), track_xl=(-2.0,-1.6), emphasis="punch",
    transitions=["scale_dissolve","whip_pan"], easing="outBack", punch_ease="outBack", motif_ease="outBack",
    parallax=(0.6,0.75), motion="dramatic", particles=(3,5)),
 "aurora_mesh": dict(weight=8, themes=["dark","dark"], accent="duotone", duo=["teal","azure","violet"],
    world=["mesh","blob","glow","grain"], accents=["brackets"],
    align="center", scale=(0.99,1.02), track_xl=(-1.8,-1.4), emphasis="word_blur",
    transitions=["blur_dissolve","scale_dissolve"], easing="inOutSine", punch_ease="outBack", motif_ease="inOutCubic",
    parallax=(0.5,0.62), motion="flow", particles=(4,7)),
 "data_room": dict(weight=8, themes=["dark","dark","light"], accent="hero",
    world=["dots","scan","glow","rings"], accents=["hud","ticks"],
    align="center", scale=(0.97,1.0), track_xl=(-1.4,-1.0), emphasis="punch",
    transitions=["mask_wipe_h","push_slide"], easing="outExpo", punch_ease="outExpo", motif_ease="outExpo",
    parallax=(0.45,0.55), motion="precise", particles=(0,0)),
 "kinetic_bold": dict(weight=9, themes=["dark","dark"], accent="hero",
    world=["grain","glow","sweep"], accents=["indexnum"],
    align="center", scale=(1.06,1.12), track_xl=(-3.0,-2.4), emphasis="word_stagger", type_weight=900,
    transitions=["whip_pan","push_slide","card_stack"], easing="outExpo", punch_ease="outBack", motif_ease="outBack",
    parallax=(0.7,0.85), motion="aggressive", particles=(0,0)),
 "magazine": dict(weight=7, themes=["light","light","dark"], accent="hero",
    world=["grain","hairgrid","glow"], accents=["rule","indexnum"],
    align="left", scale=(1.02,1.06), track_xl=(-1.6,-1.2), emphasis="block_mask",
    transitions=["mask_wipe_v","fade_clip"], easing="inOutCubic", punch_ease="outBack", motif_ease="inOutCubic",
    parallax=(0.35,0.45), motion="editorial", particles=(0,0)),
 "minimal_mono": dict(weight=8, themes=["dark","light","light"], accent="hero",
    world=["glow"], accents=[],
    align="center", scale=(0.99,1.02), track_xl=(-2.0,-1.6), emphasis="punch",
    transitions=["fade_clip","scale_dissolve"], easing="outCubic", punch_ease="outBack", motif_ease="outCubic",
    parallax=(0.3,0.4), motion="calm", particles=(0,0)),
 "duotone": dict(weight=7, themes=["dark","dark"], accent="duotone", duo=["indigo","violet","rose"],
    world=["mesh","blob","grain","vignette"], accents=["brackets"],
    align="center", scale=(1.0,1.03), track_xl=(-1.8,-1.4), emphasis="block_mask",
    transitions=["mask_wipe_diag","blur_dissolve"], easing="outExpo", punch_ease="outBack", motif_ease="inOutCubic",
    parallax=(0.55,0.68), motion="flow", particles=(3,6)),
 "signal_hud": dict(weight=6, themes=["dark","dark"], accent="hero",
    world=["dots","rings","scan","glow"], accents=["hud","ticks","radar"],
    align="center", scale=(0.98,1.01), track_xl=(-1.2,-0.9), emphasis="punch",
    transitions=["mask_wipe_h","scale_dissolve"], easing="outExpo", punch_ease="outBack", motif_ease="outExpo",
    parallax=(0.45,0.55), motion="precise", particles=(0,0)),
 "graphite": dict(weight=6, themes=["dark","dark"], accent="shift",
    world=["grain","mesh","vignette","glow"], accents=["brackets","ghost"],
    align="center", scale=(0.99,1.02), track_xl=(-2.0,-1.6), emphasis="punch",
    transitions=["fade_clip","push_slide"], easing="outCubic", punch_ease="outBack", motif_ease="outCubic",
    parallax=(0.4,0.5), motion="calm", particles=(4,6)),
}

def pick_lookbook(rng, name, recent):
    if name and name not in ("auto", None) and name in LOOKBOOKS:
        return name
    names = sorted(LOOKBOOKS.keys())
    pool = [n for n in names if n not in (recent or [])] or names
    weights = [LOOKBOOKS[n]["weight"] for n in pool]
    return rng.choices(pool, weights=weights, k=1)[0]

def resolve_theme(rng, lb, theme_hint):
    if theme_hint in ("dark", "light"): return theme_hint
    return rng.choice(lb["themes"])

def assemble_look(spec, *, kind, recent=None):
    seed = derive_seed(spec); rng = random.Random(seed)
    name = (spec.get("look") or spec.get("style")) if isinstance(spec, dict) else None
    lbn = pick_lookbook(rng, name, recent if recent is not None else load_recent())
    lb = LOOKBOOKS[lbn]
    theme = resolve_theme(rng, lb, (spec.get("theme") if isinstance(spec, dict) else None))
    font_name = _art_hint(spec, "font_pairing")
    if font_name not in FONTPAIRS:
        font_name = _roll_v2(rng, lbn, "font", FONTPAIRS, "system")
    layout_name = _art_hint(spec, "layout")
    if layout_name not in LAYOUTS:
        layout_name = _roll_v2(rng, lbn, "layout", LAYOUTS, "centered")
    tone_name = _art_hint(spec, "tone")
    if tone_name not in TONES:
        tone_name = _roll_v2(rng, lbn, "tone", TONES, "amber_signature")
    d3_name = _art_hint(spec, "d3")
    if d3_name not in D3S:
        d3_name = _roll_v2(rng, lbn, "d3", D3S, "none")
    if not any(_art_hint(spec, k) for k in ("font_pairing", "layout", "tone", "d3")):
        recent_art = load_recent_art()
        for _ in range(6):
            combo = "|".join([lbn, font_name, layout_name, tone_name, d3_name])
            if combo not in recent_art:
                break
            font_name = _roll_v2(rng, lbn, "font", FONTPAIRS, "system")
            layout_name = _roll_v2(rng, lbn, "layout", LAYOUTS, "centered")
            tone_name = _roll_v2(rng, lbn, "tone", TONES, "amber_signature")
            d3_name = _roll_v2(rng, lbn, "d3", D3S, "none")
    # grade (amber hero + tasteful variety)
    grade = {"accent": lb.get("accent", "hero")}
    if grade["accent"] == "shift": grade["shift_deg"] = rng.uniform(-6, 7)
    if grade["accent"] == "duotone": grade["duo"] = rng.choice(lb.get("duo", ["indigo"]))
    if isinstance(spec, dict) and spec.get("accent"): grade["accent"] = "hero"  # explicit hex handled in palette via amber override below
    grade["tone"] = tone_name
    # resolve world layers with seeded params
    world = []
    pc = int(round(_rng_range(rng, lb.get("particles", (0, 0)))))
    for lid in lb["world"]:
        d = {"id": lid}
        if lid == "glow": d.update(x=rng.randint(42, 58), y=rng.randint(32, 44))
        elif lid == "beam": d.update(intensity=round(rng.uniform(.10, .17), 3), angle=rng.randint(12, 24), x=rng.randint(52, 70))
        elif lid == "spotlight": d.update(intensity=round(rng.uniform(.11, .17), 3), x=rng.randint(40, 60), y=rng.randint(26, 40))
        elif lid == "grid": d.update(size=rng.choice([64, 72, 80]))
        elif lid == "blob":
            d["blobs"] = [{"x": rng.randint(16, 34), "y": rng.randint(22, 40), "c": "amber"},
                          {"x": rng.randint(66, 86), "y": rng.randint(60, 80), "c": "accent2"}]
        world.append(d)
    if pc > 0: world.append({"id": "particles", "count": pc})
    _txl = round(_rng_range(rng, lb["track_xl"]), 2)
    fp = dict(FONTPAIRS[font_name])
    track_nudge = fp.get("track", 0)
    look = dict(lookbook=lbn, seed=seed, theme=theme, grade=grade,
                world=world, accents=list(lb.get("accents", [])),
                fonts=dict(name=font_name, display=fp.get("display"), body=fp.get("body"),
                           case=fp.get("case", "none"), italic_punch=fp.get("italic_punch", False)),
                type=dict(weight=lb.get("type_weight", 800),
                          track_xl=round(_txl + track_nudge, 2), track_lg=round((_txl * 0.6) + track_nudge, 2),
                          scale=round(_rng_range(rng, lb["scale"]), 3),
                          emphasis=lb.get("emphasis", "punch")),
                layout=dict(align=lb.get("align", "center"), template=layout_name),
                d3=dict(mode=d3_name, speed=round(rng.uniform(0.14, 0.28), 3), depth=rng.randint(42, 86)),
                jitter=dict(rings_rot=round(rng.uniform(0.7, 1.2), 2), particle_seed=round(rng.uniform(1.3, 2.1), 2)))
    look["type"]["weight"] = int(fp.get("weight") or look["type"]["weight"])
    # kind-specific motion zone
    if kind == "video":
        pool = list(lb["transitions"])
        if d3_name != "none":
            pool += ["flip_3d", "zoom_blur", "iris_wipe"]
            if d3_name == "prism_rotate":
                pool.append("cube_rotate")
        primary = rng.choice(pool)
        seq = []
        for i in range(8):
            seq.append(rng.choice(pool) if (i and rng.random() < 0.34) else primary)
        sj = [dict(enter=round(rng.uniform(0.52, 0.66), 2), stagger=round(rng.uniform(0.07, 0.12), 3),
                   dir=rng.choice([-1, 1])) for _ in range(8)]
        kinetic = lb.get("emphasis", "punch")
        if font_name == "editorial_serif":
            kinetic = rng.choice(["line_rise_serif", kinetic])
        elif d3_name == "extruded_type":
            kinetic = rng.choice(["char_cascade", kinetic])
        elif font_name in ("condensed_ops", "extended_signal"):
            kinetic = rng.choice(["typewriter", "word_stagger", kinetic])
        look["motion"] = dict(personality=lb.get("motion", "calm"),
                              easings=dict(enter=lb.get("easing", "outCubic"), exit="inQuad",
                                           punch=lb.get("punch_ease", "outBack"), motif=lb.get("motif_ease", "outCubic")),
                              parallax=round(_rng_range(rng, lb["parallax"]), 2),
                              transitions=pool, transition_seq=seq, scene_jitter=sj,
                              kinetic=kinetic)
        # per-scene text placement (varies composition across the 6 beats; seeded => deterministic per run)
        base_h = "left" if layout_name in ("left_editorial", "split", "asymmetric_hero", "grid") else "center"
        per_scene = []
        for _i in range(6):
            h = rng.choices([base_h, "center", "left", "right"], weights=[5, 3, 2, 1])[0]
            v = rng.choices(["center", "top", "bottom"], weights=[6, 2, 2])[0]
            per_scene.append({"h": h, "v": v})
        look["layout"]["per_scene"] = per_scene
        try:
            import apex_worlds
            _topic = (spec.get("topic") or spec.get("id") or "") if isinstance(spec, dict) else ""
            look["world_setpiece"] = apex_worlds.pick(_topic, rng)
        except Exception:
            look["world_setpiece"] = None
    return look

def choose_look(spec, *, kind, recent=None):
    spec = spec if isinstance(spec, dict) else {}
    return assemble_look(spec, kind=kind, recent=recent)

# ============================================================ TL.style for video
def build_style_block(look):
    if not look: return None
    m = look.get("motion", {}); j = look.get("jitter", {})
    em = m.get("kinetic", "punch")
    kin = {"mode": em,
           "unit_stagger": 0.026 if em in ("char_cascade", "typewriter") else (0.05 if em == "word_stagger" else 0.06),
           "unit_blur": 7 if em == "word_blur" else 0,
           "unit_y": 22}
    return dict(
        ease=m.get("easings", dict(enter="outCubic", exit="inQuad", punch="outBack", motif="outCubic")),
        cam=dict(zoom=0.05, pan=10), parallax=m.get("parallax", 0.45),
        kinetic=kin, trans_dur=0.45, motif_ease=m.get("easings", {}).get("motif", "outCubic"),
        d3=look.get("d3", dict(mode="none")),
        world=dict(rings_rot=j.get("rings_rot", 1.1), particle_seed=j.get("particle_seed", 1.7),
                   blob_amp=18, beam_sweep=0.05, scan_speed=0.0, grid_drift=10, mesh_amp=8))

# ============================================================ anti-repeat memory
def load_recent():
    try:
        with open(MEMORY, encoding="utf-8") as f: return (json.load(f) or {}).get("recent", [])
    except Exception:
        return []
def load_recent_art():
    try:
        with open(MEMORY, encoding="utf-8") as f: return (json.load(f) or {}).get("recent_art", [])
    except Exception:
        return []
def remember_look(look):
    try:
        nm = look.get("lookbook")
        try:
            data = json.load(open(MEMORY, encoding="utf-8"))
        except Exception:
            data = {}
        rec = data.get("recent", [])
        if not rec or rec[-1] != nm:
            rec.append(nm)
        rec = rec[-6:]
        combo = "|".join([nm or "", look.get("fonts", {}).get("name", ""),
                          look.get("layout", {}).get("template", ""),
                          look.get("grade", {}).get("tone", ""),
                          look.get("d3", {}).get("mode", "")])
        art = data.get("recent_art", [])
        if combo and (not art or art[-1] != combo):
            art.append(combo)
        with open(MEMORY, "w", encoding="utf-8") as f: json.dump({"recent": rec, "recent_art": art[-8:]}, f)
    except Exception:
        pass
