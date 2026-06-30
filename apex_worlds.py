# -*- coding: utf-8 -*-
"""
apex_worlds.py — concept-custom background SET-PIECES for the video renderer.

Each set-piece is ONE inline SVG (viewBox 0 0 W H) of brand-tinted shapes placed
BEHIND the text (low opacity), giving every video a bespoke "world" that matches its
concept ("many things in the background, custom to the concept"). Elements tagged with
class `wd` get a deterministic per-frame drift from the render(t) hook in
build_today_video.RENDER_JS (pure function of t — no Math.random/Date.now). Brand:
mono ink/off-white + a single amber accent only.

Contract:
  pick(topic_text, rng) -> name            # keyword -> set-piece (seeded fallback)
  world_css(P) -> css                       # container + element styling (theme-aware)
  world_html(name, P, W, H, seed) -> svg    # the set-piece SVG (deterministic by seed)
"""
import math, random

# topic keyword -> set-piece name
KEYWORDS = [
    (("post", "posting", "daily", "content", "noise", "feed", "social", "calendar", "publish", "algorithm"), "feed_cards"),
    (("speed", "fast", "slow", "load", "loading", "performance", "latency", "second", "lag"), "gauges"),
    (("funnel", "leak", "leaking", "convert", "conversion", "drop", "bucket", "pipeline"), "funnel_drips"),
    (("cost", "price", "budget", "spend", "money", "rs ", "roi", "cheap", "invoice", "rupee", "vanish"), "coin_field"),
    (("seo", "rank", "ranking", "compound", "growth", "traffic", "scale", "trend", "outrank", "patience"), "stair_climb"),
    (("system", "network", "build", "devops", "app", "site", "website", "architecture", "uptime", "path"), "node_net"),
    (("audit", "scan", "signal", "hidden", "detect", "reveal", "clarity", "visible"), "scan_grid"),
]
DEFAULTS = ["node_net", "stair_climb", "gauges", "feed_cards"]

def pick(topic_text, rng):
    t = (topic_text or "").lower()
    for kws, name in KEYWORDS:
        if any(k in t for k in kws):
            return name
    return (rng or random.Random(0)).choice(DEFAULTS)

def world_css(P):
    # The whole set-piece sits behind the stage text; faint so the headline always wins.
    return (".world-set{position:absolute;inset:0;z-index:1;pointer-events:none;opacity:.9}"
            ".world-set .wd{will-change:transform}")

# ---- helpers ----
def _hex(h): h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def _rgba(hexc, a): r, g, b = _hex(hexc); return f"rgba({r},{g},{b},{a})"

def _open(W, H):
    return f'<svg class="world-set" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none">'

# ---- set-pieces (each returns an inline SVG string) ----
def _feed_cards(P, W, H, rng):
    """Drifting social 'post' cards — for content/noise/social concepts."""
    ink = P["text_primary"]; amber = P["amber"]; hair = P["hairline"]
    cards = []
    for i in range(9):
        x = rng.randint(40, W - 240); y = rng.randint(int(H * 0.10), int(H * 0.86))
        w = rng.randint(150, 210); h = int(w * 0.62)
        acc = (i % 4 == 0)
        stroke = _rgba(amber, .5) if acc else _rgba(ink, .14)
        bars = "".join(f'<rect x="{x+16}" y="{y+44+k*16}" width="{w-32-(k*22)}" height="6" rx="3" fill="{_rgba(ink,.10)}"/>' for k in range(3))
        cards.append(
            f'<g class="wd" data-i="{i}" opacity="{0.5 if acc else 0.32}">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" stroke="{stroke}" stroke-width="1.5" fill="{_rgba(ink,.02)}"/>'
            f'<circle cx="{x+22}" cy="{y+24}" r="9" fill="{_rgba(amber,.5) if acc else _rgba(ink,.16)}"/>'
            f'<rect x="{x+38}" y="{y+18}" width="{w-70}" height="7" rx="3" fill="{_rgba(ink,.16)}"/>'
            f'{bars}</g>')
    return _open(W, H) + "".join(cards) + "</svg>"

def _gauges(P, W, H, rng):
    """Telemetry gauges + tick arcs — for speed/performance concepts."""
    ink = P["text_primary"]; amber = P["amber"]
    out = []
    for i in range(4):
        cx = rng.randint(120, W - 120); cy = rng.randint(int(H * 0.14), int(H * 0.82)); r = rng.randint(60, 120)
        ticks = ""
        for d in range(0, 181, 20):
            a = math.radians(d); c, s = math.cos(a), math.sin(a)
            col = _rgba(amber, .55) if d <= 60 else _rgba(ink, .14)
            ticks += (f'<line x1="{cx-(r)*c:.0f}" y1="{cy-(r)*s:.0f}" x2="{cx-(r-12)*c:.0f}" y2="{cy-(r-12)*s:.0f}" '
                      f'stroke="{col}" stroke-width="2"/>')
        out.append(f'<g class="wd" data-i="{i}" opacity="0.4">'
                   f'<path d="M{cx-r},{cy} A{r},{r} 0 0 1 {cx+r},{cy}" stroke="{_rgba(ink,.12)}" stroke-width="2" fill="none"/>'
                   f'{ticks}<circle cx="{cx}" cy="{cy}" r="4" fill="{_rgba(amber,.6)}"/></g>')
    return _open(W, H) + "".join(out) + "</svg>"

def _funnel_drips(P, W, H, rng):
    """A large faint funnel + falling drip dots leaking out the bottom — for leaky-funnel concepts."""
    ink = P["text_primary"]; amber = P["amber"]
    cx = int(W * 0.5)
    fy = int(H * 0.16); fb = int(H * 0.52)
    funnel = (f'<path d="M{cx-300},{fy} L{cx+300},{fy} L{cx+70},{fb} L{cx-70},{fb} Z" '
              f'stroke="{_rgba(ink,.13)}" stroke-width="2" fill="{_rgba(ink,.02)}"/>')
    drips = []
    for i in range(10):
        dx = cx + rng.randint(-60, 60); dy = rng.randint(fb + 20, H - 60); rr = rng.randint(4, 9)
        col = _rgba(amber, .5) if i % 3 == 0 else _rgba(ink, .18)
        drips.append(f'<circle class="wd" data-i="{i}" cx="{dx}" cy="{dy}" r="{rr}" fill="{col}"/>')
    return _open(W, H) + f'<g opacity="0.5">{funnel}</g>' + "".join(drips) + "</svg>"

def _coin_field(P, W, H, rng):
    """Scattered coin discs + Rs marks — for cost/ROI/money concepts."""
    ink = P["text_primary"]; amber = P["amber"]
    out = []
    for i in range(11):
        x = rng.randint(50, W - 50); y = rng.randint(int(H * 0.10), int(H * 0.88)); rx = rng.randint(26, 50)
        acc = (i % 3 == 0)
        col = _rgba(amber, .5) if acc else _rgba(ink, .14)
        out.append(f'<g class="wd" data-i="{i}" opacity="{0.5 if acc else 0.3}">'
                   f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{int(rx*0.42)}" stroke="{col}" stroke-width="2" fill="{_rgba(ink,.02)}"/>'
                   f'<ellipse cx="{x}" cy="{y-6}" rx="{rx}" ry="{int(rx*0.42)}" stroke="{col}" stroke-width="2" fill="none"/></g>')
    return _open(W, H) + "".join(out) + "</svg>"

def _stair_climb(P, W, H, rng):
    """Rising stair/bar field + ascending dotted curve — for SEO/compounding/growth concepts."""
    ink = P["text_primary"]; amber = P["amber"]
    base = int(H * 0.74); x0 = int(W * 0.12); bw = 70; gap = 26
    bars = []
    for i in range(8):
        bh = int(40 + i * (i + 2) * 5.5); x = x0 + i * (bw + gap)
        if x > W - 80: break
        acc = (i == 7 or i == 6)
        bars.append(f'<rect class="wd" data-i="{i}" x="{x}" y="{base-bh}" width="{bw}" height="{bh}" rx="6" '
                    f'fill="{_rgba(amber,.4) if acc else _rgba(ink,.10)}" opacity="0.55"/>')
    return _open(W, H) + "".join(bars) + "</svg>"

def _node_net(P, W, H, rng):
    """Connected node network — for system/network/build concepts."""
    ink = P["text_primary"]; amber = P["amber"]
    pts = [(rng.randint(80, W - 80), rng.randint(int(H * 0.10), int(H * 0.88))) for _ in range(11)]
    lines = []
    for i, (x, y) in enumerate(pts):
        # connect each node to its nearest 2 by index distance (cheap, deterministic)
        for j in (i + 1, i + 3):
            if j < len(pts):
                x2, y2 = pts[j]
                lines.append(f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="{_rgba(ink,.08)}" stroke-width="1.3"/>')
    nodes = []
    for i, (x, y) in enumerate(pts):
        acc = (i % 4 == 0)
        nodes.append(f'<circle class="wd" data-i="{i}" cx="{x}" cy="{y}" r="{7 if acc else 5}" '
                     f'fill="{_rgba(amber,.6) if acc else _rgba(ink,.22)}"/>')
    return _open(W, H) + f'<g opacity="0.6">{"".join(lines)}</g>' + "".join(nodes) + "</svg>"

def _scan_grid(P, W, H, rng):
    """Radar/scan rings + scattered blips — for audit/signal/clarity concepts."""
    ink = P["text_primary"]; amber = P["amber"]
    cx, cy = int(W * 0.5), int(H * 0.42)
    rings = "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{_rgba(ink,.10)}" stroke-width="1.4" fill="none"/>'
                    for r in (140, 250, 360, 470))
    blips = []
    for i in range(9):
        a = rng.uniform(0, 6.28); rr = rng.uniform(60, 460)
        x = cx + math.cos(a) * rr; y = cy + math.sin(a) * rr
        acc = (i % 3 == 0)
        blips.append(f'<circle class="wd" data-i="{i}" cx="{x:.0f}" cy="{y:.0f}" r="{6 if acc else 4}" '
                     f'fill="{_rgba(amber,.6) if acc else _rgba(ink,.2)}"/>')
    return _open(W, H) + f'<g opacity="0.55">{rings}</g>' + "".join(blips) + "</svg>"

SETPIECES = {
    "feed_cards": _feed_cards, "gauges": _gauges, "funnel_drips": _funnel_drips,
    "coin_field": _coin_field, "stair_climb": _stair_climb, "node_net": _node_net, "scan_grid": _scan_grid,
}

def world_html(name, P, W, H, seed=0):
    fn = SETPIECES.get(name)
    if not fn:
        return ""
    return fn(P, W, H, random.Random((seed or 0) ^ 0x5A17))
