# -*- coding: utf-8 -*-
"""Local SVG icon helpers for Apex Studio.

Icons are loaded from assets/icons/lucide when fetch_assets.py has run. A small
fallback set keeps specs renderable before the first online asset refresh.
"""
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(ROOT, "assets", "icons", "lucide")

FALLBACKS = {
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "code": '<path d="m16 18 6-6-6-6"/><path d="m8 6-6 6 6 6"/>',
    "cloud": '<path d="M17.5 19H8a6 6 0 1 1 5.7-8.1A4.5 4.5 0 1 1 17.5 19Z"/>',
    "smartphone": '<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/>',
    "chart": '<path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-7"/>',
    "trending-up": '<path d="m3 17 6-6 4 4 8-8"/><path d="M14 7h7v7"/>',
    "funnel": '<path d="M3 4h18l-7 8v6l-4 2v-8Z"/>',
    "coins": '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6"/><path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "megaphone": '<path d="m3 11 18-5v12L3 13Z"/><path d="M7 14v5a2 2 0 0 0 2 2h1"/>',
    "zap": '<path d="M13 2 3 14h8l-1 8 11-14h-8Z"/>',
    "shield-check": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-5"/>',
    "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "radar": '<path d="M19.1 4.9A10 10 0 1 1 4.9 19.1"/><path d="M12 12 21 3"/><circle cx="12" cy="12" r="2"/><path d="M12 6a6 6 0 0 1 6 6"/>',
}

_CACHE = None
ALIASES = {
    "bar-chart-3": "chart-bar",
    "check-circle-2": "circle-check",
    "globe-2": "globe",
    "layers-3": "layers",
    "line-chart": "chart-line",
    "cursor-click": "mouse-pointer-click",
    "chart": "chart-line",
}

def _inner(svg):
    svg = re.sub(r"<\?xml.*?\?>", "", svg, flags=re.S)
    m = re.search(r"<svg\b[^>]*>(.*)</svg>", svg, flags=re.S | re.I)
    body = m.group(1) if m else svg
    body = re.sub(r'\s(width|height)="[^"]*"', "", body)
    body = re.sub(r'stroke="[^"]*"', 'stroke="currentColor"', body)
    body = re.sub(r'fill="(?!none)[^"]*"', 'fill="none"', body)
    return body.strip()

def load_icons():
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    icons = dict(FALLBACKS)
    if os.path.isdir(ICON_DIR):
        for name in os.listdir(ICON_DIR):
            if not name.lower().endswith(".svg"):
                continue
            key = os.path.splitext(name)[0]
            try:
                with open(os.path.join(ICON_DIR, name), encoding="utf-8") as f:
                    icons[key] = _inner(f.read())
            except Exception:
                pass
    _CACHE = icons
    return icons

def names():
    return sorted(load_icons())

def icon_svg(name, *, size=28, cls="ic", accent=False, stroke_w=2.15):
    key = str(name).replace("_", "-")
    key = ALIASES.get(key, key)
    body = load_icons().get(key) or FALLBACKS.get(key) or FALLBACKS["target"]
    tone = " accent" if accent else ""
    return (
        f'<svg class="{cls}{tone}" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="currentColor" stroke-width="{stroke_w}" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{body}</svg>'
    )

def css(P):
    return f"""
.ic{{display:inline-block;vertical-align:middle;color:{P['text_primary']};will-change:transform,opacity;filter:drop-shadow(0 8px 20px rgba(0,0,0,.18))}}
.ic.accent{{color:{P['amber']}}}
.icon-row{{display:flex;justify-content:center;align-items:center;gap:16px;margin-bottom:24px}}
.icon-corner{{position:absolute;right:18px;top:10px;display:flex;gap:12px;opacity:.92}}
.icon-bullets{{display:flex;gap:12px;flex-wrap:wrap;justify-content:center;margin-top:20px}}
.icon-bullet{{display:inline-flex;align-items:center;gap:9px;color:{P['text_secondary']};font-size:18px;font-weight:700}}
.chip .ic{{width:17px;height:17px;margin-right:7px;transform:translateY(2px);filter:none}}
.constel{{display:flex;align-items:center;justify-content:center;gap:0;margin-bottom:30px}}
.ctile{{display:inline-flex;align-items:center;justify-content:center;width:74px;height:74px;border-radius:18px;
  border:1px solid {P['hairline']};background:rgba(140,140,150,.05);box-shadow:0 16px 34px rgba(0,0,0,.22)}}
.ctile .ic{{width:34px;height:34px;filter:none;color:{P['text_primary']}}}
.ctile.accent{{border-color:{P['amber']};background:rgba(255,190,11,.07);box-shadow:0 0 0 1px {P['amber']},0 16px 34px rgba(0,0,0,.26)}}
.ctile.accent .ic{{color:{P['amber']}}}
.cwire{{width:34px;height:2px;background:linear-gradient(90deg,transparent,{P['hairline']},transparent)}}
"""
