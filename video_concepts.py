# -*- coding: utf-8 -*-
"""
video_concepts.py — daily concept registry for the Apex video system (v3).

"Brand-lock + creative-flex": brand (colors/fonts/lockup/format) is fixed in
build_today_video.py; each concept here supplies the day's CONTENT + art direction:
kicker, 6-beat scenes (kinetic text), narration (text + pace + emotion), a hero
VECTOR MOTIF (animated inline SVG + JS), the music mood, and the caption.

Add a concept, set TODAY, and the whole video (animation/voice/music) changes.
"""

# ---- animated hero motifs (inline SVG + JS hook window.motifSet(i, p)) ----
# JS runs in the page scope after RENDER_JS (so E, c01, lerp, q are available).

def motif_speedometer(P):
    # a gauge: track arc + amber redline + ticks + needle (rotated via setAttribute) + value
    import math
    cx, cy, r = 220, 212, 168
    def pt(deg):
        a = math.radians(deg)
        return (cx + r*math.cos(a), cy - r*math.sin(a))
    x0, y0 = pt(180); x1, y1 = pt(0); xr, yr = pt(46)
    ticks = ""
    for d in range(0, 181, 18):
        a = math.radians(d); c, s = math.cos(a), math.sin(a)
        col = P["amber"] if d <= 46 else P["text_tertiary"]
        ticks += (f'<line x1="{cx+(r-4)*c:.1f}" y1="{cy-(r-4)*s:.1f}" '
                  f'x2="{cx+(r-20)*c:.1f}" y2="{cy-(r-20)*s:.1f}" stroke="{col}" stroke-width="3"/>')
    return (
        f'<svg class="gauge" width="440" height="250" viewBox="0 0 440 250" fill="none">'
        f'<path d="M{x0:.0f},{y0:.0f} A{r},{r} 0 0 1 {x1:.0f},{y1:.0f}" stroke="{P["hairline"]}" stroke-width="8" stroke-linecap="round"/>'
        f'<path id="redarc" d="M{xr:.0f},{yr:.0f} A{r},{r} 0 0 1 {x1:.0f},{y1:.0f}" stroke="{P["amber"]}" stroke-width="8" stroke-linecap="round" opacity="0.35"/>'
        f'{ticks}'
        f'<line id="needle" x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy-r+18}" stroke="{P["text_primary"]}" stroke-width="7" stroke-linecap="round"/>'
        f'<circle cx="{cx}" cy="{cy}" r="13" fill="{P["amber"]}"/>'
        f'<text id="gaugeval" x="{cx}" y="{cy-44}" text-anchor="middle" font-family="Segoe UI,Arial" font-weight="800" font-size="58" fill="{P["amber"]}" letter-spacing="-2"></text>'
        f'</svg>')

MOTIF_JS_SPEEDOMETER = r"""
window.motifSet=function(i,p){
  var w=document.getElementById('motif'); if(!w)return;
  var nd=document.getElementById('needle'), val=document.getElementById('gaugeval'), red=document.getElementById('redarc');
  var show=0, v=0.16, label='';
  if(i==0){ show=1; v=0.16; label=''; }                                   // idle
  else if(i==2){ show=1; var u=E.outCubic(c01((p-0.12)/0.7)); v=lerp(0.16,0.97,u); label=Math.round(8*u)+'s'; } // sweep to redline, count to 8s
  else if(i==4){ show=1; var u=E.inOutCubic(c01((p-0.1)/0.6)); v=lerp(0.95,0.2,u); label='fast'; }            // fix pulls back to green
  var camS = (i==2)?1.06:1.0;
  w.style.opacity=show; w.style.transform='translateX(-50%) scale('+(show?camS:0.9)+')';
  var ang=-80+160*v;
  if(nd)nd.setAttribute('transform','rotate('+ang.toFixed(2)+' 220 212)');
  if(val)val.textContent=label;
  if(red)red.style.opacity=(v>0.62?1:0.35);
};
"""

def motif_countring(P):
    import math
    cx, cy, r = 150, 150, 112; circ = 2*math.pi*r
    return (
        f'<svg class="ring" width="300" height="300" viewBox="0 0 300 300" fill="none">'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{P["hairline"]}" stroke-width="10"/>'
        f'<circle id="cring" cx="{cx}" cy="{cy}" r="{r}" stroke="{P["amber"]}" stroke-width="10" stroke-linecap="round" '
        f'stroke-dasharray="{circ:.1f}" stroke-dashoffset="0" transform="rotate(-90 {cx} {cy})"/>'
        f'<text id="cnum" x="{cx}" y="{cy+2}" text-anchor="middle" dominant-baseline="central" '
        f'font-family="Segoe UI,Arial" font-weight="800" font-size="120" fill="{P["text_primary"]}" letter-spacing="-4">10</text>'
        f'<text x="{cx}" y="{cy+74}" text-anchor="middle" font-family="Segoe UI,Arial" font-weight="700" font-size="20" '
        f'fill="{P["text_tertiary"]}" letter-spacing="5">SECONDS</text></svg>')

MOTIF_JS_COUNTRING = r"""
window.motifSet=function(i,p){
  var w=document.getElementById('motif'); if(!w)return;
  var ring=document.getElementById('cring'), num=document.getElementById('cnum');
  var C=2*Math.PI*112, show=0, u=0, n=10;
  if(i==0){ show=1; u=0; n=10; }
  else if(i==2){ show=1; u=E.outCubic(c01((p-0.1)/0.78)); n=Math.ceil(10*(1-u)); }
  w.style.opacity=show; w.style.transform='translateX(-50%) scale('+(i==2?1.05:1.0)+')';
  if(ring)ring.setAttribute('stroke-dashoffset',(C*u).toFixed(1));
  if(num){ num.textContent=n; num.setAttribute('fill', n<=3 ? '#FFBE0B' : '#ECEDF0'); }
};
"""

# ---- expanded motif library (visibility via MS.indexOf(i): -1 hide, 0 idle, >=1 animate) ----
def motif_bar_grow(P):
    bars=[0.42,0.66,0.52,0.82,1.0]; x0=70; bw=44; gap=24; base=222
    rects="".join(
        f'<rect id="bar{j}" x="{x0+j*(bw+gap)}" y="{base}" width="{bw}" height="0" rx="5" '
        f'fill="{P["amber"] if j==len(bars)-1 else P["text_primary"]}" opacity="0.92"/>'
        for j in range(len(bars)))
    return (f'<svg class="bars" width="400" height="250" viewBox="0 0 400 250" fill="none">'
            f'<line x1="50" y1="{base}" x2="372" y2="{base}" stroke="{P["hairline"]}" stroke-width="2"/>{rects}</svg>')
MOTIF_JS_BAR_GROW = r"""
window.motifSet=function(i,p){var w=document.getElementById('motif');if(!w)return;
 var k=window.MS?MS.indexOf(i):(i==0?0:i==2?1:-1);if(k<0){w.style.opacity=0;return;}
 var base=222,maxh=176,fr=[0.42,0.66,0.52,0.82,1.0];
 w.style.opacity=1;w.style.transform='translateX(-50%) scale('+(k>=1?1.04:1.0)+')';
 for(var j=0;j<5;j++){var b=document.getElementById('bar'+j);if(!b)continue;
   var u=(k>=1)?E.outBack(c01((p-0.12-j*0.06)/0.6)):0;var h=maxh*fr[j]*u;
   b.setAttribute('height',(h>0?h:0).toFixed(1));b.setAttribute('y',(base-(h>0?h:0)).toFixed(1));}
};
"""

def motif_line_trend(P):
    return (f'<svg class="ltr" width="400" height="250" viewBox="0 0 400 250" fill="none">'
            f'<line x1="56" y1="214" x2="360" y2="214" stroke="{P["hairline"]}" stroke-width="2"/>'
            f'<polyline id="ltp" points="60,210 120,196 180,168 240,176 300,120 356,70" fill="none" '
            f'stroke="{P["amber"]}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle id="ltd" cx="356" cy="70" r="9" fill="{P["amber"]}" opacity="0"/></svg>')
MOTIF_JS_LINE_TREND = r"""
window.motifSet=function(i,p){var w=document.getElementById('motif');if(!w)return;
 var k=window.MS?MS.indexOf(i):(i==0?0:i==2?1:-1);if(k<0){w.style.opacity=0;return;}
 var ln=document.getElementById('ltp'),dt=document.getElementById('ltd');if(!ln)return;
 w.style.opacity=1;w.style.transform='translateX(-50%) scale('+(k>=1?1.04:1.0)+')';
 var L=ln.getTotalLength();ln.style.strokeDasharray=L;
 var u=(k>=1)?E.outCubic(c01((p-0.1)/0.74)):0;ln.style.strokeDashoffset=(L*(1-u)).toFixed(1);
 if(dt)dt.setAttribute('opacity',(u>0.92?1:0).toString());
};
"""

def motif_growth_curve(P):
    return (f'<svg class="gcv" width="410" height="250" viewBox="0 0 410 250" fill="none">'
            f'<line x1="58" y1="216" x2="362" y2="216" stroke="{P["hairline"]}" stroke-width="2"/>'
            f'<line x1="58" y1="216" x2="58" y2="38" stroke="{P["hairline"]}" stroke-width="2"/>'
            f'<polyline id="gcp" points="60,212 130,206 195,190 250,158 296,104 346,44" fill="none" '
            f'stroke="{P["amber"]}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle id="gcd" cx="346" cy="44" r="9" fill="{P["amber"]}" opacity="0"/></svg>')
MOTIF_JS_GROWTH = r"""
window.motifSet=function(i,p){var w=document.getElementById('motif');if(!w)return;
 var k=window.MS?MS.indexOf(i):(i==0?0:i==2?1:-1);if(k<0){w.style.opacity=0;return;}
 var ln=document.getElementById('gcp'),dt=document.getElementById('gcd');if(!ln)return;
 w.style.opacity=1;w.style.transform='translateX(-50%) scale('+(k>=1?1.05:1.0)+')';
 var L=ln.getTotalLength();ln.style.strokeDasharray=L;
 var u=(k>=1)?E.inOutCubic(c01((p-0.1)/0.76)):0;ln.style.strokeDashoffset=(L*(1-u)).toFixed(1);
 if(dt)dt.setAttribute('opacity',(u>0.9?1:0).toString());
};
"""

def motif_funnel(P):
    widths=[300,238,176,120]; cx=200; y0=54; gap=52; h=38
    bars="".join(
        f'<rect id="fn{j}" x="{cx-wd/2:.0f}" y="{y0+j*gap}" width="{wd}" height="{h}" rx="6" '
        f'fill="{P["amber"] if j==len(widths)-1 else P["text_primary"]}" opacity="0"/>'
        for j,wd in enumerate(widths))
    return f'<svg class="fnl" width="400" height="280" viewBox="0 0 400 280" fill="none">{bars}</svg>'
MOTIF_JS_FUNNEL = r"""
window.motifSet=function(i,p){var w=document.getElementById('motif');if(!w)return;
 var k=window.MS?MS.indexOf(i):(i==0?0:i==2?1:-1);if(k<0){w.style.opacity=0;return;}
 w.style.opacity=1;w.style.transform='translateX(-50%) scale('+(k>=1?1.04:1.0)+')';
 for(var j=0;j<4;j++){var b=document.getElementById('fn'+j);if(!b)continue;
   var u=(k>=1)?E.outCubic(c01((p-0.12-j*0.12)/0.5)):0;
   b.setAttribute('opacity',(0.16+0.76*c01(u)).toFixed(3));}
};
"""

def motif_donut(P):
    import math; cx,cy,r=150,150,108; circ=2*math.pi*r
    return (f'<svg class="dnt" width="300" height="300" viewBox="0 0 300 300" fill="none">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{P["hairline"]}" stroke-width="14"/>'
            f'<circle id="dpr" cx="{cx}" cy="{cy}" r="{r}" stroke="{P["amber"]}" stroke-width="14" stroke-linecap="round" '
            f'stroke-dasharray="{circ:.1f}" stroke-dashoffset="{circ:.1f}" transform="rotate(-90 {cx} {cy})"/>'
            f'<text id="dpn" x="{cx}" y="{cy+4}" text-anchor="middle" dominant-baseline="central" '
            f'font-family="Segoe UI,Arial" font-weight="800" font-size="74" fill="{P["text_primary"]}" letter-spacing="-3">0%</text></svg>')
MOTIF_JS_DONUT = r"""
window.motifSet=function(i,p){var w=document.getElementById('motif');if(!w)return;
 var k=window.MS?MS.indexOf(i):(i==0?0:i==2?1:-1);if(k<0){w.style.opacity=0;return;}
 var ring=document.getElementById('dpr'),num=document.getElementById('dpn');var C=2*Math.PI*108,T=0.73;
 w.style.opacity=1;w.style.transform='translateX(-50%) scale('+(k>=1?1.05:1.0)+')';
 var u=(k>=1)?E.outCubic(c01((p-0.1)/0.78)):0;var frac=T*u;
 if(ring)ring.setAttribute('stroke-dashoffset',(C*(1-frac)).toFixed(1));
 if(num)num.textContent=Math.round(100*frac)+'%';
};
"""

def motif_arrow(P):
    return (f'<svg class="arw" width="300" height="280" viewBox="0 0 300 280" fill="none">'
            f'<rect x="120" y="118" width="60" height="150" rx="8" fill="{P["text_primary"]}" opacity="0.22"/>'
            f'<g id="arwg"><path d="M150,40 L226,150 L176,150 L176,250 L124,250 L124,150 L74,150 Z" fill="{P["amber"]}"/></g></svg>')
MOTIF_JS_ARROW = r"""
window.motifSet=function(i,p){var w=document.getElementById('motif');if(!w)return;
 var k=window.MS?MS.indexOf(i):(i==0?0:i==2?1:-1);if(k<0){w.style.opacity=0;return;}
 var g=document.getElementById('arwg');
 w.style.opacity=1;w.style.transform='translateX(-50%) scale('+(k>=1?1.05:1.0)+')';
 var u=(k>=1)?E.outBack(c01((p-0.12)/0.6)):0;
 if(g){g.setAttribute('transform','translate(0 '+((1-c01(u))*70).toFixed(1)+')');g.style.opacity=c01(u*1.3).toFixed(3);}
};
"""

def motif_coins(P):
    cx=150; ew=84; eh=26; base=240; gap=30
    coins="".join(
        f'<ellipse id="cn{j}" cx="{cx}" cy="{base-j*gap}" rx="{ew}" ry="{eh}" '
        f'fill="{P["amber"] if j==4 else P["text_primary"]}" opacity="0"/>'
        for j in range(5))
    return f'<svg class="coins" width="300" height="290" viewBox="0 0 300 290" fill="none">{coins}</svg>'
MOTIF_JS_COINS = r"""
window.motifSet=function(i,p){var w=document.getElementById('motif');if(!w)return;
 var k=window.MS?MS.indexOf(i):(i==0?0:i==2?1:-1);if(k<0){w.style.opacity=0;return;}
 w.style.opacity=1;w.style.transform='translateX(-50%) scale('+(k>=1?1.04:1.0)+')';
 for(var j=0;j<5;j++){var c=document.getElementById('cn'+j);if(!c)continue;
   var u=(k>=1)?E.outBack(c01((p-0.1-j*0.09)/0.5)):0;
   c.setAttribute('opacity',(c01(u)*(j==4?0.96:0.85)).toFixed(3));
   c.setAttribute('transform','translate(0 '+((1-c01(u))*18).toFixed(1)+')');}
};
"""

def motif_radar(P):
    cx,cy=150,150
    rings="".join(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{P["ring"]}" stroke-width="1.5"/>' for r in (44,82,118))
    cross=(f'<line x1="{cx-118}" y1="{cy}" x2="{cx+118}" y2="{cy}" stroke="{P["ring"]}" stroke-width="1"/>'
           f'<line x1="{cx}" y1="{cy-118}" x2="{cx}" y2="{cy+118}" stroke="{P["ring"]}" stroke-width="1"/>')
    return (f'<svg class="rdr" width="300" height="300" viewBox="0 0 300 300" fill="none">{rings}{cross}'
            f'<line id="rsw" x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy-118}" stroke="{P["amber"]}" stroke-width="3" stroke-linecap="round"/>'
            f'<circle id="rbl" cx="{cx}" cy="{cy-82}" r="0" fill="{P["amber"]}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="5" fill="{P["amber"]}"/></svg>')
MOTIF_JS_RADAR = r"""
window.motifSet=function(i,p){var w=document.getElementById('motif');if(!w)return;
 var k=window.MS?MS.indexOf(i):(i==0?0:i==2?1:-1);if(k<0){w.style.opacity=0;return;}
 var sw=document.getElementById('rsw'),bl=document.getElementById('rbl');
 w.style.opacity=1;w.style.transform='translateX(-50%) scale('+(k>=1?1.04:1.0)+')';
 var u=(k>=1)?c01((p-0.05)/0.9):0;var ang=u*340;
 if(sw)sw.setAttribute('transform','rotate('+ang.toFixed(1)+' 150 150)');
 var br=(u>0.62&&u<0.86)?E.outBack(c01((u-0.62)/0.12))*7:(u>=0.86?7:0);
 if(bl)bl.setAttribute('r',(br>0?br:0).toFixed(1));
};
"""

CONCEPTS = {
    "site_speed": dict(
        id="site_speed",
        kicker="Site Speed System",
        music_mood="driving",
        caption=(
            "Sound on. \U0001f50a Your site is fast — on YOUR phone. That's the trap.\n\n"
            "Your real buyer is on a mid-range Android, on 4G, weak signal. If your site takes 8 seconds to load there, "
            "about half of them leave before they read a single word — no error, no bounce alert, just silent lost leads.\n\n"
            "You don't have a traffic problem. You have a version of your site you've never seen.\n\n"
            "Apex IT makes it fast on real devices; Apex Marketings turns that speed into leads.\n\n"
            "DM \"AUDIT\" and we'll load your site on a real phone, on 4G, and show you exactly what you're missing — free.\n\n"
            "When did you last open your own site on a slow connection?\n\n"
            "#WebPerformance #PageSpeed #LeadGeneration #CoreWebVitals #DigitalMarketing #smallbusinesspakistan #founders #SEO"),
        # (text, speaking-speed)  -- pace conveys emotion: urgent vs deliberate
        narration=[
            ("Your website is fast. On your phone, on office wifi. That's the only version you ever test.", 1.0),
            ("But your real buyer? A mid-range Android, on four G, with a weak signal.", 1.02),
            ("If it takes eight seconds to load there, half of them are gone before they read a word.", 1.04),
            ("You don't have a traffic problem. You have a version of your site you've never seen.", 0.96),
            ("Apex I-T makes it fast on real devices. Apex Marketings turns that speed into leads.", 1.0),
            ("D-M AUDIT, and we'll load your site on a real phone, and show you what you're missing.", 1.0),
        ],
        scenes=[
            # s1 — hook (motif idle above)
            ('<h1 class="hxl">Fast. On <b class="punch" data-at="0.40">your</b> phone.</h1>'
             '<p class="sub">The only version you ever test.</p>'),
            # s2 — real buyer
            ('<div class="tag">Your real buyer</div>'
             '<h2 class="hlg">A mid-range Android.<br>On <b class="punch" data-at="0.45">4G</b>. Weak signal.</h2>'),
            # s3 — the gauge sweeps (motif hero)
            ('<h2 class="hlg">8 seconds to load.<br><b class="punch" data-at="0.5">Half</b> already gone.</h2>'
             '<p class="sub">No error. No alert. Just silent lost leads.</p>'),
            # s4 — reframe
            ('<h2 class="hxl">Not a traffic problem.<br>A <b class="punch" data-at="0.55">version</b><br>you’ve never seen.</h2>'),
            # s5 — fix (motif pulls back to fast)
            ('<div class="tag">The fix</div>'
             '<h2 class="hlg">Make the slow version<br><b class="punch" data-at="0.5">disappear</b>.</h2>'
             '<div class="split">'
             '<div class="col"><div class="lab"><span class="dot dn"></span>Build</div><div class="brand">Apex IT Solutions</div>'
             '<div class="chips"><span class="chip n">Real-device speed</span><span class="chip n">Core Web Vitals</span></div></div>'
             '<div class="divider"></div>'
             '<div class="col"><div class="lab"><span class="dot da"></span>Growth</div><div class="brand">Apex Marketings</div>'
             '<div class="chips"><span class="chip a">Mobile CRO</span><span class="chip a">Faster funnels</span></div></div>'
             '</div>'),
            # s6 — CTA
            ('<h2 class="hlg">Test it on a<br><b class="punch" data-at="0.45">real</b> phone.</h2>'
             '<div class="ctabox">DM <b>&ldquo;AUDIT&rdquo;</b> &mdash; free, on 4G, today.</div>'),
        ],
        motif_scenes=[0, 2, 4],                 # scenes where the gauge shows
        motif_svg=motif_speedometer,
        motif_js=MOTIF_JS_SPEEDOMETER,
    ),
    "clarity": dict(
        id="clarity",
        kicker="Clarity System",
        music_mood="tense",
        caption=(
            "Sound on. \U0001f50a Your homepage gets ~10 seconds to make sense — most waste 8 of them.\n\n"
            "A visitor lands, scans, and asks one thing: “Am I in the right place?” If your page can't answer that fast, "
            "they leave — and you blame the traffic.\n\n"
            "You don't have a traffic problem. You have a clarity problem.\n\n"
            "Apex IT builds a page that answers in seconds; Apex Marketings makes the offer impossible to miss.\n\n"
            "DM \"AUDIT\" and we'll screen-record a stranger using your site — you'll see exactly where it loses them. Free.\n\n"
            "Would a stranger know what you do in 10 seconds?\n\n"
            "#CRO #WebDesign #LandingPages #ConversionRate #DigitalMarketing #smallbusinesspakistan #founders #UX"),
        narration=[
            ("Your homepage gets about ten seconds to make sense. Most waste eight of them.", 1.0),
            ("A visitor lands, scans, and asks one question. Am I in the right place?", 1.0),
            ("If they can't answer that in ten seconds, they're gone. And you blame the traffic.", 1.03),
            ("You don't have a traffic problem. You have a clarity problem.", 0.97),
            ("Apex I-T builds a page that answers fast. Apex Marketings makes the offer impossible to miss.", 1.0),
            ("D-M AUDIT, and we'll screen-record a stranger using your site. You'll see it instantly.", 1.0),
        ],
        scenes=[
            ('<h1 class="hxl">Your homepage gets<br><b class="punch" data-at="0.40">10 seconds</b>.</h1>'),
            ('<div class="tag">The scan</div>'
             '<h2 class="hlg">Land. Scan.<br><b class="punch" data-at="0.45">One</b> question:</h2>'
             '<p class="sub">&ldquo;Am I in the right place?&rdquo;</p>'),
            ('<h2 class="hlg">No answer in 10s?<br>They&rsquo;re <b class="punch" data-at="0.5">gone</b>.</h2>'
             '<p class="sub">And you blame the traffic.</p>'),
            ('<h2 class="hxl">Not a traffic problem.<br>A <b class="punch" data-at="0.55">clarity</b> problem.</h2>'),
            ('<div class="tag">The fix</div>'
             '<h2 class="hlg">Make the offer<br><b class="punch" data-at="0.45">obvious</b>.</h2>'
             '<div class="split">'
             '<div class="col"><div class="lab"><span class="dot dn"></span>Build</div><div class="brand">Apex IT Solutions</div>'
             '<div class="chips"><span class="chip n">Clear structure</span><span class="chip n">Fast first paint</span></div></div>'
             '<div class="divider"></div>'
             '<div class="col"><div class="lab"><span class="dot da"></span>Growth</div><div class="brand">Apex Marketings</div>'
             '<div class="chips"><span class="chip a">Sharp offer copy</span><span class="chip a">One clear CTA</span></div></div>'
             '</div>'),
            ('<h2 class="hlg">See it for<br><b class="punch" data-at="0.45">yourself</b>.</h2>'
             '<div class="ctabox">DM <b>&ldquo;AUDIT&rdquo;</b> &mdash; we screen-record a stranger using your site.</div>'),
        ],
        motif_scenes=[0, 2],
        motif_svg=motif_countring,
        motif_js=MOTIF_JS_COUNTRING,
    ),
}

MOTIFS = {
    "speedometer": (motif_speedometer, MOTIF_JS_SPEEDOMETER),
    "countring": (motif_countring, MOTIF_JS_COUNTRING),
    "bar_grow": (motif_bar_grow, MOTIF_JS_BAR_GROW),
    "line_trend": (motif_line_trend, MOTIF_JS_LINE_TREND),
    "growth_curve": (motif_growth_curve, MOTIF_JS_GROWTH),
    "funnel": (motif_funnel, MOTIF_JS_FUNNEL),
    "donut_progress": (motif_donut, MOTIF_JS_DONUT),
    "arrow_up": (motif_arrow, MOTIF_JS_ARROW),
    "roi_coins": (motif_coins, MOTIF_JS_COINS),
    "radar_sweep": (motif_radar, MOTIF_JS_RADAR),
    "none": (lambda P: "", ""),
}

# topic/headline keyword -> motif (used when the spec leaves motif_name "auto"/absent)
MOTIF_KEYWORDS = {
    "speedometer":   ["speed", "fast", "slow", "load", "loading", "performance", "second", "latency", "page speed"],
    "countring":     ["countdown", "10 second", "ticking", "clock", "time to decide"],
    "bar_grow":      ["revenue", "growth", "increase", "more leads", "double", "sales", "results", "traffic"],
    "line_trend":    ["trend", "over time", "month", "trajectory", "trending", "graph"],
    "growth_curve":  ["compound", "exponential", "scale", "snowball", "long term", "long-term"],
    "funnel":        ["funnel", "leads", "conversion", "drop off", "drop-off", "stages", "leak", "leaking"],
    "donut_progress":["percent", "%", "rate", "share", "half", "portion", "majority"],
    "arrow_up":      ["rise", "rising", "higher", "boost", "lift", "go up", "grow"],
    "roi_coins":     ["cost", "price", "budget", "spend", "money", "cheap", "invoice", "roi", "rupee", "rs "],
    "radar_sweep":   ["audit", "scan", "detect", "find", "hidden", "invisible", "discover", "reveal"],
}

import random as _random
def _all_headlines(spec):
    out = []; v = (spec or {}).get("video") or {}
    for b in (v.get("scenes") or []):
        for h in (b.get("headline") or []): out.append(str(h))
    return out
def auto_motif(spec, look=None, rng=None):
    text = " ".join([str((spec or {}).get("topic", ""))] + _all_headlines(spec)).lower()
    if rng is None: rng = _random.Random((look or {}).get("seed", 0))
    hits = [(m, sum(1 for kw in ks if kw in text)) for m, ks in MOTIF_KEYWORDS.items()]
    hits = [h for h in hits if h[1] > 0]
    if hits:
        best = max(h[1] for h in hits)
        return rng.choice(sorted([m for m, c in hits if c == best]))
    return rng.choice(["bar_grow", "line_trend", "arrow_up", "donut_progress", "growth_curve", "none"])

TODAY = "clarity"

def get_today():
    return CONCEPTS[TODAY]
