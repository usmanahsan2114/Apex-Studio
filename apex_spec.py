# -*- coding: utf-8 -*-
"""
apex_spec.py — the `day_spec.json` data contract for the Apex daily post system.

One JSON describes the whole day's post and drives BOTH generators:
  - build_today_pack.py  (5-slide image carousel, light+dark x LinkedIn/FB)
  - build_today_video.py (reel: VO + music + animated motif)

This module: load(), validate(), and the HTML-assembly helpers that turn the
structured JSON into the exact inner-HTML the generators expect (so there is NO
source patching — set env APEX_SPEC=path and the generators read this).

Schema (see SCHEMA_EXAMPLE at the bottom for a full worked example):
{
  "id","date","topic","theme":"dark|light",
  "carousel": {
    "kicker",
    "slides": [
      {motif?, headline:[..], sub},                                   # s1 cover (motif = "X -> Y" stamp)
      {tag, headline:[..], sub, meter?:{head,left,right}},            # s2 problem
      {headline:[..], sub},                                          # s3 reframe
      {tag, headline:[..], build_chips:[2], growth_chips:[2]},        # s4 system
      {headline:[..], sub, cta}                                       # s5 CTA (cta should contain "AUDIT")
    ],
    "linkedin": {caption, hashtags:[<=3]},
    "fb": {caption, hashtags:[8-15]}
  },
  "video": {
    "kicker", "music_mood":"driving|uplift|tense", "caption",
    "narration": [ {text, speed} x6 ],
    "motif_name":"speedometer|house_key|hourglass|funnel|none", "motif_scenes":[ints],
    "scenes": [                                                       # 6 beats (structured, NOT raw html)
      {stamp?, tag?, headline:[..], sub?, count?, count_from?, build_chips?, growth_chips?, cta?, big?, punch_at?}
    ]
  }
}
In any headline/sub, wrap a key word in **double asterisks** -> amber. In video headlines the FIRST
**word** becomes the animated scale-punch. A cta containing "AUDIT" auto-bolds it.
"""
import json, re

# ---------------- text helpers ----------------
def _amp(s): return s.replace(" & ", " &amp; ") if (s and " & " in s) else (s or "")
def bold_static(s):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", _amp(s))
def bold_punch(s, at="0.45"):
    seen = [False]
    def rep(m):
        if not seen[0]:
            seen[0] = True; return f'<b class="punch" data-at="{at}">{m.group(1)}</b>'
        return f"<b>{m.group(1)}</b>"
    return re.sub(r"\*\*(.+?)\*\*", rep, _amp(s))
def _lines(arr, bolder): return "<br>".join(bolder(x) for x in (arr or []))
def _chip_label(c):
    return c.get("label", "") if isinstance(c, dict) else c
def _chip_icon(c):
    name = c.get("icon") if isinstance(c, dict) else None
    if not name:  # auto-derive an icon from the chip label so plain-string chips are richer too
        name = _chip_icon_guess(_chip_label(c))
    if not name: return ""
    try:
        import apex_icons
        return apex_icons.icon_svg(name, size=17, cls="ic chip-ic", accent=False)
    except Exception:
        return ""
def _chips(arr, cls):
    return "".join('<span class="chip %s">%s%s</span>' % (cls, _chip_icon(c), _chip_label(c)) for c in (arr or []))
def _arrowify(m):
    m = (m or "").strip()
    return (m.split("->", 1)[0].strip() + ' <span class="arr">&rarr;</span> ' + m.split("->", 1)[1].strip()) if "->" in m else m

def _icons(items, slot):
    items = [x for x in (items or []) if isinstance(x, dict) and x.get("slot", "inline") == slot and x.get("name")]
    if not items: return ""
    try:
        import apex_icons
        bits = []
        for it in items[:4]:
            bits.append(apex_icons.icon_svg(it["name"], size=int(it.get("size", 32)), accent=bool(it.get("accent"))))
    except Exception:
        return ""
    if slot == "corner":
        return '<div class="icon-corner">%s</div>' % "".join(bits[:2])
    if slot == "bullet":
        return '<div class="icon-bullets">%s</div>' % "".join('<span class="icon-bullet">%s</span>' % b for b in bits[:3])
    return '<div class="icon-row">%s</div>' % "".join(bits[:3])

# ---------------- auto graphic density (icons derived from a scene's own text) ----------------
# Maps founder-felt vocabulary -> a vendored Lucide icon (falls back to "target" if absent).
ICON_KEYWORDS = [
    (("post", "posting", "daily", "calendar", "schedule", "feed", "publish"), "calendar"),
    (("noise", "megaphone", "amplify", "broadcast", "shout", "social", "content", "reach"), "megaphone"),
    (("lead", "leads", "buyer", "customer", "audience", "client", "prospect"), "target"),
    (("convert", "conversion", "click", "cta", "action", "signup", "sign-up"), "mouse-pointer-click"),
    (("money", "rs ", "budget", "spend", "cost", "price", "roi", "cheap", "invoice", "rupee", "vanish"), "coins"),
    (("speed", "fast", "slow", "load", "loading", "performance", "latency", "second", "lag"), "gauge"),
    (("seo", "rank", "ranking", "traffic", "google", "organic", "keyword", "outrank"), "trending-up"),
    (("site", "website", "page", "web", "landing", "homepage", "build"), "code"),
    (("funnel", "leak", "leaking", "drop", "pipeline", "bucket"), "funnel"),
    (("growth", "scale", "compound", "increase", "revenue", "grow"), "trending-up"),
    (("app", "mobile", "phone", "android", "ios"), "smartphone"),
    (("data", "analytics", "metric", "metrics", "dashboard", "report", "algorithm"), "chart"),
    (("trust", "shield", "secure", "reliable", "uptime", "devops", "cloud", "server"), "shield-check"),
    (("time", "deadline", "clock", "hour", "minute", "wait", "patience", "tomorrow"), "clock"),
    (("audit", "scan", "detect", "signal", "hidden", "reveal"), "radar"),
    (("search", "discover", "visible", "attention", "find", "recall", "memory", "forgotten"), "search"),
    (("strategy", "system", "path", "plan", "framework", "structure"), "route"),
]
ICON_DEFAULTS = ["trending-up", "target", "zap"]

def _scene_text(b):
    parts = list(b.get("headline", []) or []) + [b.get("sub", ""), b.get("tag", ""), b.get("stamp", ""), b.get("cta", "")]
    return " ".join(str(x) for x in parts).lower()

def _auto_icon_names(text, n=3):
    out = []
    for kws, name in ICON_KEYWORDS:
        if any(k in text for k in kws) and name not in out:
            out.append(name)
        if len(out) >= n: break
    for d in ICON_DEFAULTS:
        if len(out) >= n: break
        if d not in out: out.append(d)
    return out[:n]

def _constellation(names, accent_idx=1, size=38):
    try:
        import apex_icons
    except Exception:
        return ""
    tiles = []
    for i, nm in enumerate(names):
        acc = (i == accent_idx)
        tiles.append('<span class="ctile%s">%s</span>' % (" accent" if acc else "",
                     apex_icons.icon_svg(nm, size=size, cls="ic", accent=acc)))
    return '<div class="constel">' + '<span class="cwire"></span>'.join(tiles) + '</div>'

def _auto_constellation(b):
    """A keyword-derived icon constellation for any scene that has no explicit icons."""
    return _constellation(_auto_icon_names(_scene_text(b)))

def _chip_icon_guess(label):
    return _auto_icon_names(str(label).lower(), 1)[0]

# ---------------- carousel (build_today_pack SLIDES) ----------------
def _motif_stamp(m):
    m = (m or "").strip()
    return ('<div class="stamp"><span class="sdot"></span> %s</div>\n     ' % _arrowify(m)) if m else ""
def _meter(mt):
    if not mt or not mt.get("head"): return ""
    return ('\n     <div class="meter"><div class="mhead">%s</div>\n'
            '       <div class="mtrack"><div class="mfill"></div><div class="mknob"></div></div>\n'
            '       <div class="mends"><span>%s</span><span class="goal">%s</span></div></div>'
            % (mt["head"], mt.get("left", ""), mt.get("right", "")))
def _cta(s): return bold_static((s or "").replace('"AUDIT"', '<b>&ldquo;AUDIT&rdquo;</b>'))

def build_carousel_slides(c, look=None):
    # `look` (from apex_art) art-directs world/layout/type at the doc() level; the 5-slide
    # semantic structure here stays identical so content + brand lockup are unchanged.
    s = c["slides"]; g = lambda i, k, d=None: s[i].get(k, d)
    s1 = ('%s%s<h1 class="hxl">%s</h1>\n     <p class="sub">%s</p>%s\n     <div class="swipe">Swipe &rarr;</div>'
          % (_icons(g(0, "icons", []), "corner"), _motif_stamp(g(0, "motif")) + (_icons(g(0, "icons", []), "inline") if g(0, "icons") else _auto_constellation(s[0])), _lines(g(0, "headline", []), bold_static), bold_static(g(0, "sub", "")), _icons(g(0, "icons", []), "bullet")))
    s2 = ('<div class="tag">%s</div>\n     <h2 class="hlg">%s</h2>\n     <p class="sub">%s</p>%s'
          % (g(1, "tag", ""), _lines(g(1, "headline", []), bold_static), bold_static(g(1, "sub", "")), _icons(g(1, "icons", []), "bullet") + _meter(g(1, "meter"))))
    s3 = ('%s<h2 class="hxl">%s</h2>\n     <p class="sub">%s</p>%s'
          % ((_icons(g(2, "icons", []), "inline") if g(2, "icons") else _auto_constellation(s[2])), _lines(g(2, "headline", []), bold_static), bold_static(g(2, "sub", "")), _icons(g(2, "icons", []), "bullet")))
    s4 = ('%s<div class="tag">%s</div>\n     <h2 class="hlg">%s</h2>\n     <div class="split">\n'
          '       <div class="col"><div class="lab"><span class="dot dn"></span>Build</div><div class="brand">Apex IT Solutions</div>\n'
          '         <div class="chips">%s</div></div>\n       <div class="divider"></div>\n'
          '       <div class="col"><div class="lab"><span class="dot da"></span>Growth</div><div class="brand">Apex Marketings</div>\n'
          '         <div class="chips">%s</div></div>\n     </div>'
          % (_icons(g(3, "icons", []), "corner"), g(3, "tag", ""), _lines(g(3, "headline", []), bold_static), _chips(g(3, "build_chips", []), "n"), _chips(g(3, "growth_chips", []), "a")))
    s5 = ('%s<h2 class="hlg">%s</h2>\n     <p class="sub">%s</p>\n     <div class="ctabox">%s</div>'
          % ((_icons(g(4, "icons", []), "inline") if g(4, "icons") else _auto_constellation(s[4])), _lines(g(4, "headline", []), bold_static), bold_static(g(4, "sub", "")), _cta(g(4, "cta", ""))))
    return [s1, s2, s3, s4, s5]

def _caption(text, tags):
    text = (text or "").strip()
    if tags and tags[0].lower() not in text.lower(): text = text + "\n\n" + " ".join(tags)
    return text.rstrip() + "\n"
def carousel_captions(c):
    li = c.get("linkedin", {}); fb = c.get("fb", {})
    return _caption(li.get("caption", ""), li.get("hashtags", [])), _caption(fb.get("caption", ""), fb.get("hashtags", []))

# ---------------- video (build_today_video concept) ----------------
def build_video_scenes(beats):
    out = []
    for bi, b in enumerate(beats):
        p = ['<div class="bgnum">%02d</div>' % (bi + 1)]  # big editorial scene numeral (behind text)
        if b.get("icons"):
            p.append(_icons(b.get("icons"), "corner"))
        if b.get("stamp"):
            p.append('<div class="stamp"><span class="sdot"></span> %s</div>' % _arrowify(b["stamp"]))
        if b.get("tag"):
            p.append('<div class="tag">%s</div>' % b["tag"])
        if b.get("icons"):
            p.append(_icons(b.get("icons"), "inline"))
        elif not (b.get("build_chips") or b.get("growth_chips")):
            # auto graphic density: every non-chip scene gets a keyword-derived icon constellation
            p.append(_auto_constellation(b))
        hl = b.get("headline", []); cls = "hxl" if (b.get("big") or len(hl) >= 3) else "hlg"
        p.append('<h2 class="%s">%s</h2>' % (cls, _lines(hl, lambda s: bold_punch(s, str(b.get("punch_at", "0.45"))))))
        if b.get("count") is not None:
            cf = b.get("count_from", 100)
            p.append('<div class="count" data-from="%s" data-to="%s">%s</div>' % (cf, b["count"], cf))
        if b.get("sub"):
            p.append('<p class="sub">%s</p>' % bold_static(b["sub"]))
        if b.get("icons"):
            p.append(_icons(b.get("icons"), "bullet"))
        if b.get("build_chips") or b.get("growth_chips"):
            p.append('<div class="split"><div class="col"><div class="lab"><span class="dot dn"></span>Build</div>'
                     '<div class="brand">Apex IT Solutions</div><div class="chips">%s</div></div><div class="divider"></div>'
                     '<div class="col"><div class="lab"><span class="dot da"></span>Growth</div>'
                     '<div class="brand">Apex Marketings</div><div class="chips">%s</div></div></div>'
                     % (_chips(b.get("build_chips", []), "n"), _chips(b.get("growth_chips", []), "a")))
        if b.get("cta"):
            p.append('<div class="ctabox">%s</div>' % _cta(b["cta"]))
        out.append("\n     ".join(p))
    return out

def build_video_concept(spec, MOTIFS, look=None):
    v = spec["video"]; name = v.get("motif_name", "auto")
    if name in ("auto", None) or name not in MOTIFS:      # resolve auto/unknown -> keyword pick
        import video_concepts as _VC
        name = _VC.auto_motif(spec, look)
    fn, js = MOTIFS.get(name, MOTIFS.get("none"))
    layers = []
    for layer in v.get("motif_layers", []) or []:
        lname = layer.get("motif_name") or layer.get("name")
        if lname in MOTIFS:
            layers.append(dict(layer, motif_name=lname, motif_svg=MOTIFS[lname][0]))
    return dict(id=spec.get("id", "day"), kicker=v["kicker"], music_mood=v.get("music_mood", "driving"),
                caption=v.get("caption", ""),
                narration=[(n["text"], float(n.get("speed", 1.0))) for n in v["narration"]],
                scenes=build_video_scenes(v["scenes"]),
                motif_scenes=v.get("motif_scenes", []), motif_svg=fn, motif_js=js, motif_name=name,
                motif_layers=layers, art=v.get("art", {}))

# ---------------- load / validate ----------------
def load(path):
    with open(path, encoding="utf-8") as f: return json.load(f)

def validate(spec):
    e = []
    if not isinstance(spec, dict): return False, ["spec must be a JSON object"]
    if "carousel" not in spec and "video" not in spec:
        e.append("need a 'carousel' and/or 'video' section")
    if spec.get("theme", "dark") not in ("dark", "light"):
        e.append("theme must be 'dark' or 'light'")
    c = spec.get("carousel")
    if c is not None:
        if not c.get("kicker"): e.append("carousel.kicker is required")
        sl = c.get("slides", [])
        if len(sl) != 5: e.append("carousel.slides must have exactly 5 entries")
        for i, s in enumerate(sl):
            if not s.get("headline"): e.append(f"carousel.slides[{i}].headline is required")
        if not (sl and len(sl) > 3 and len(sl[3].get("build_chips", [])) and len(sl[3].get("growth_chips", []))):
            e.append("carousel.slides[3] needs build_chips + growth_chips")
        for k in ("linkedin", "fb"):
            if not c.get(k, {}).get("caption"): e.append(f"carousel.{k}.caption is required")
        if len(c.get("linkedin", {}).get("hashtags", [])) > 3:
            e.append("carousel.linkedin.hashtags must be <= 3")
    v = spec.get("video")
    if v is not None:
        if not v.get("kicker"): e.append("video.kicker is required")
        if len(v.get("narration", [])) != 6: e.append("video.narration must have 6 lines")
        if len(v.get("scenes", [])) != 6: e.append("video.scenes must have 6 beats")
        if v.get("music_mood", "driving") not in ("driving", "uplift", "tense"):
            e.append("video.music_mood must be driving|uplift|tense")
        # v2 art-direction fields are optional and intentionally lenient. Invalid
        # values fall back during art selection so older and hand-authored specs do not break.
        if v.get("art") is not None and not isinstance(v.get("art"), dict):
            e.append("video.art must be an object when present")
    # optional art-direction fields — all optional, lenient (never block on these)
    if "seed" in spec:
        try: int(spec["seed"])
        except Exception: e.append("seed must be an integer")
    if spec.get("art_direction") is not None and not isinstance(spec.get("art_direction"), dict):
        e.append("art_direction must be an object when present")
    _look = spec.get("look") or spec.get("style")
    if _look and _look != "auto":
        try:
            import apex_art
            if _look not in apex_art.LOOKBOOKS:
                e.append("look must be 'auto' or one of: " + ", ".join(sorted(apex_art.LOOKBOOKS)))
        except Exception:
            pass
    return (len(e) == 0), e

VALID_MOTIFS = ["auto", "speedometer", "countring", "bar_grow", "line_trend", "growth_curve",
                "funnel", "donut_progress", "arrow_up", "roi_coins", "radar_sweep",
                "stopwatch", "shield_check", "network_nodes", "stack_layers",
                "cursor_click", "signal_bars", "none"]
MUSIC_MOODS = ["driving", "uplift", "tense"]
