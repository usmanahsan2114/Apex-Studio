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
def _chips(arr, cls): return "".join('<span class="chip %s">%s</span>' % (cls, c) for c in (arr or []))
def _arrowify(m):
    m = (m or "").strip()
    return (m.split("->", 1)[0].strip() + ' <span class="arr">&rarr;</span> ' + m.split("->", 1)[1].strip()) if "->" in m else m

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

def build_carousel_slides(c):
    s = c["slides"]; g = lambda i, k, d=None: s[i].get(k, d)
    s1 = ('%s<h1 class="hxl">%s</h1>\n     <p class="sub">%s</p>\n     <div class="swipe">Swipe &rarr;</div>'
          % (_motif_stamp(g(0, "motif")), _lines(g(0, "headline", []), bold_static), bold_static(g(0, "sub", ""))))
    s2 = ('<div class="tag">%s</div>\n     <h2 class="hlg">%s</h2>\n     <p class="sub">%s</p>%s'
          % (g(1, "tag", ""), _lines(g(1, "headline", []), bold_static), bold_static(g(1, "sub", "")), _meter(g(1, "meter"))))
    s3 = ('<h2 class="hxl">%s</h2>\n     <p class="sub">%s</p>'
          % (_lines(g(2, "headline", []), bold_static), bold_static(g(2, "sub", ""))))
    s4 = ('<div class="tag">%s</div>\n     <h2 class="hlg">%s</h2>\n     <div class="split">\n'
          '       <div class="col"><div class="lab"><span class="dot dn"></span>Build</div><div class="brand">Apex IT Solutions</div>\n'
          '         <div class="chips">%s</div></div>\n       <div class="divider"></div>\n'
          '       <div class="col"><div class="lab"><span class="dot da"></span>Growth</div><div class="brand">Apex Marketings</div>\n'
          '         <div class="chips">%s</div></div>\n     </div>'
          % (g(3, "tag", ""), _lines(g(3, "headline", []), bold_static), _chips(g(3, "build_chips", []), "n"), _chips(g(3, "growth_chips", []), "a")))
    s5 = ('<h2 class="hlg">%s</h2>\n     <p class="sub">%s</p>\n     <div class="ctabox">%s</div>'
          % (_lines(g(4, "headline", []), bold_static), bold_static(g(4, "sub", "")), _cta(g(4, "cta", ""))))
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
    for b in beats:
        p = []
        if b.get("stamp"):
            p.append('<div class="stamp"><span class="sdot"></span> %s</div>' % _arrowify(b["stamp"]))
        if b.get("tag"):
            p.append('<div class="tag">%s</div>' % b["tag"])
        hl = b.get("headline", []); cls = "hxl" if (b.get("big") or len(hl) >= 3) else "hlg"
        p.append('<h2 class="%s">%s</h2>' % (cls, _lines(hl, lambda s: bold_punch(s, str(b.get("punch_at", "0.45"))))))
        if b.get("count") is not None:
            cf = b.get("count_from", 100)
            p.append('<div class="count" data-from="%s" data-to="%s">%s</div>' % (cf, b["count"], cf))
        if b.get("sub"):
            p.append('<p class="sub">%s</p>' % bold_static(b["sub"]))
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

def build_video_concept(spec, MOTIFS):
    v = spec["video"]; fn, js = MOTIFS.get(v.get("motif_name", "none"), MOTIFS.get("none"))
    return dict(id=spec.get("id", "day"), kicker=v["kicker"], music_mood=v.get("music_mood", "driving"),
                caption=v.get("caption", ""),
                narration=[(n["text"], float(n.get("speed", 1.0))) for n in v["narration"]],
                scenes=build_video_scenes(v["scenes"]),
                motif_scenes=v.get("motif_scenes", []), motif_svg=fn, motif_js=js)

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
    return (len(e) == 0), e

VALID_MOTIFS = ["speedometer", "house_key", "hourglass", "funnel", "none"]
MUSIC_MOODS = ["driving", "uplift", "tense"]
