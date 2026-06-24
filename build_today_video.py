# -*- coding: utf-8 -*-
"""
build_today_video.py (v3) — daily concept-customized premium vector REEL:
Kokoro voiceover (natural/human) + procedural per-video MUSIC + synthesized SFX,
an animated hero VECTOR MOTIF, richer motion, for Instagram (1080x1920) + LinkedIn (1080x1350).

The day's CONTENT + art direction (scenes, narration, motif, music mood, caption)
comes from video_concepts.py (get_today()). Brand/design is locked via build_today_pack.

Engines (offline/free): Kokoro (kokoro-onnx) VO, numpy procedural music + SFX, Chrome frame-scrub, imageio-ffmpeg.

Usage:
  python build_today_video.py smoke   # synth VO+music, build timeline, 1 still/beat + audio preview
  python build_today_video.py         # full render -> generated_images/video/
"""
import json, os, shutil, subprocess, sys, tempfile, wave
import numpy as np
from scipy.signal import resample_poly, butter, lfilter
from PIL import Image
import imageio_ffmpeg
import build_today_pack as pack
import video_concepts as VC
import apex_spec
import apex_art

def get_concept():
    sp = os.environ.get("APEX_SPEC")
    spec = apex_spec.load(sp) if (sp and os.path.exists(sp)) else None
    look = apex_art.choose_look(spec or {}, kind="video")
    if spec and spec.get("video"):
        print("APEX_SPEC video loaded:", spec.get("id", "?"), "| look:", look["lookbook"], look["theme"], flush=True)
        c = apex_spec.build_video_concept(spec, VC.MOTIFS, look=look)
    else:
        c = dict(VC.get_today())
    c["look"] = look
    return c

ROOT, OUT = pack.ROOT, pack.OUT
VIDEO_DIR = os.path.join(OUT, "video")
TMP = os.path.join(tempfile.gettempdir(), "apex_vid")
KDIR = os.path.join(ROOT, "assets", "kokoro")
FF = imageio_ffmpeg.get_ffmpeg_exe()
CHROME = pack.CHROME
FPS, SR, THEME = 30, 48000, "dark"
VOICE = "af_heart"                      # warm, natural, engaging (kokoro v1.0)
LEADIN, TAIL, INTRO, OUTRO = 0.40, 0.62, 0.6, 1.1

ASPECTS = {
    "instagram": dict(w=1080, h=1920, safe_top=130, safe_bottom=340, title=120, lg=84, sub=40, motif_top=300, out="instagram_reel.mp4"),
    "linkedin":  dict(w=1080, h=1350, safe_top=60,  safe_bottom=72,  title=104, lg=74, sub=34, motif_top=180, out="linkedin_video.mp4"),
}

# ===================== VOICEOVER (Kokoro, offline) =====================
_KOKORO = None
def _kokoro():
    global _KOKORO
    if _KOKORO is None:
        from kokoro_onnx import Kokoro
        _KOKORO = Kokoro(os.path.join(KDIR, "kokoro-v1.0.onnx"), os.path.join(KDIR, "voices-v1.0.bin"))
    return _KOKORO

def synth_line(text, speed):
    s, sr = _kokoro().create(text, voice=VOICE, speed=speed, lang="en-us")
    s = np.asarray(s, np.float32)
    if sr != SR:
        s = resample_poly(s, SR, sr).astype(np.float32)
    p = np.max(np.abs(s)) + 1e-9
    return (s / p * 0.85).astype(np.float32)

# ===================== MUSIC (procedural, per mood) =====================
def _adsr(n, a, d, s, r):
    a, d, r = int(a*SR), int(d*SR), int(r*SR); sn = max(0, n-a-d-r)
    e = np.concatenate([np.linspace(0,1,a,endpoint=False) if a else [], np.linspace(1,s,d,endpoint=False) if d else [],
                        np.full(sn, s), np.linspace(s,0,r) if r else []])
    return np.pad(e, (0, max(0, n-len(e))))[:n]
def _lp(x, cut):
    b, a = butter(2, min(0.99, cut/(SR/2)), "low"); return lfilter(b, a, x)
def _note(semi): return 440.0 * 2**((semi-9)/12.0)
def _tone(freq, dur, kind, amp, env):
    n = int(dur*SR); t = np.arange(n)/SR
    w = (2*((t*freq) % 1)-1) if kind == "saw" else np.sin(2*np.pi*freq*t)
    return w*_adsr(n, *env)*amp

def make_music(mood, seconds):
    n = int(seconds*SR); out = np.zeros(n)
    P = {"driving": dict(root=-5, bpm=120, prog=[0,-2,-5,-7], bright=2600, minor=True,  arp=True),
         "uplift":  dict(root=0,  bpm=110, prog=[0,5,7,5],    bright=3200, minor=False, arp=True),
         "tense":   dict(root=-7, bpm=92,  prog=[0,-3,-5,-3], bright=1500, minor=True,  arp=False)}.get(mood, None)
    if P is None: P = {"root":-5,"bpm":112,"prog":[0,-2,-5,-7],"bright":2600,"minor":True,"arp":True}
    iv = [0,3,7,10] if P["minor"] else [0,4,7,11]
    beat = 60/P["bpm"]; bar = beat*4; nb = int(np.ceil(seconds/bar))
    for b in range(nb):
        root = P["root"] + P["prog"][b % len(P["prog"])]; start = int(b*bar*SR)
        pad = np.zeros(int(bar*SR))
        for k in iv[:3]:
            tt = _tone(_note(root+k), bar, "saw", 0.10, (0.4,0.3,0.7,0.6)); pad[:len(tt)] += tt[:len(pad)]
        seg = _lp(pad, P["bright"]) + _tone(_note(root-12), bar, "sine", 0.22, (0.02,0.2,0.7,0.3))[:len(pad)]
        if P["arp"]:
            for i in range(8):
                a = _tone(_note(root+12+iv[i % len(iv)]), beat/2, "sine", 0.06, (0.005,0.06,0,0.02))
                s0 = int(i*(bar/8)*SR); seg[s0:s0+len(a)] += a[:max(0, len(seg)-s0)]
        e = min(n, start+len(seg)); out[start:e] += seg[:e-start]
    out = out/(np.max(np.abs(out))+1e-9)*0.7
    f = int(0.8*SR); out[:f] *= np.linspace(0,1,f); out[-f:] *= np.linspace(1,0,f)
    return out.astype(np.float32)

# ===================== SFX (numpy) =====================
def _band(x, lo, hi):
    b, a = butter(2, [lo/(SR/2), hi/(SR/2)], "band"); return lfilter(b, a, x).astype(np.float32)
def whoosh(d=.5):
    n=int(d*SR); x=_band(np.random.default_rng(7).standard_normal(n),250,4500)
    return (x/np.max(np.abs(x)+1e-9)*(np.interp(np.linspace(0,1,n),[0,.35,1],[0,1,0])**1.5)*0.7).astype(np.float32)
def tick(d=.05):
    n=int(d*SR); t=np.arange(n)/SR; return (np.sin(2*np.pi*2200*t)*_adsr(n,.001,.02,0,.02)*0.7).astype(np.float32)
def thud(d=.36):
    n=int(d*SR); t=np.arange(n)/SR; p=92*np.exp(-3.2*t)
    return (np.sin(2*np.pi*np.cumsum(p)/SR)*_adsr(n,.002,.12,.18,.2)*0.95).astype(np.float32)
def riser(d=1.2):
    n=int(d*SR); t=np.arange(n)/SR; p=120*(900/120)**(t/d); saw=2*((np.cumsum(p)/SR)%1)-1
    return (saw*(np.linspace(0,1,n)**2)*0.5).astype(np.float32)
def chime(d=.9):
    n=int(d*SR); t=np.arange(n)/SR; o=np.zeros(n)
    for i,f in enumerate((880,1320,1760)): o+=np.sin(2*np.pi*f*t+2*np.sin(2*np.pi*f*0.5*t))*(0.6**i)
    return (o/np.max(np.abs(o)+1e-9)*_adsr(n,.004,.3,.1,.4)*0.8).astype(np.float32)
SFX={"whoosh":whoosh,"tick":tick,"thud":thud,"riser":riser,"chime":chime}

def cues(tl):
    C=[]; S=tl["scenes"]
    def add(t,n,**kw): C.append((round(t,3),n,kw))
    add(0.0,"whoosh",gain=0.4); add(0.5,"tick",gain=0.4)
    for i,s in enumerate(S):
        add(s["start"],"whoosh",gain=0.42); add(s["start"]+s["punch"],"thud",gain=0.7)
    if len(S)>2: add(S[2]["vo_at"]+0.15,"riser",gain=0.4)               # gauge sweep
    if len(S)>4:
        for dt in (0.4,0.7,1.0,1.3): add(S[4]["vo_at"]+dt,"tick",gain=0.4)
    if len(S)>5: add(S[5]["vo_at"]+0.7,"chime",gain=0.55)
    add(tl["total"]-0.5,"whoosh",gain=0.36)
    return C

def write_wav(path, mono):
    pcm=(np.clip(mono,-1,1)*32767).astype(np.int16)
    with wave.open(path,"wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

def build_sfx(tl, path):
    n=int((tl["total"]+1)*SR); buf=np.zeros(n,np.float32); cache={}
    for t,name,kw in cues(tl):
        if name not in cache: cache[name]=SFX[name]()
        sig=cache[name]; i=int(t*SR); j=min(n,i+len(sig)); buf[i:j]+=sig[:j-i]*kw.get("gain",1.0)
    buf=np.tanh(buf*0.9); write_wav(path, buf[:int(tl["total"]*SR)]); return path

# ===================== TIMELINE (VO-driven; bakes per-scene art-direction) =====================
def build_timeline(durs, look=None):
    sc=[]; t=INTRO
    mot=(look or {}).get("motion", {}) or {}
    seq=mot.get("transition_seq", []); sj=mot.get("scene_jitter", [])
    for i,d in enumerate(durs):
        dur=LEADIN+d+TAIL
        sc.append(dict(id=f"s{i+1}", start=round(t,3), end=round(t+dur,3),
                       vo_at=round(t+LEADIN,3), punch=round(LEADIN+0.30,3),
                       trans=(seq[i] if i < len(seq) else "fade_clip"),
                       enter=(sj[i]["enter"] if i < len(sj) else 0.60),
                       stag=(sj[i]["stagger"] if i < len(sj) else 0.10),
                       dir=(sj[i]["dir"] if i < len(sj) else 1)))
        t+=dur
    tl=dict(total=round(t+OUTRO,3), fps=FPS, scenes=sc)
    style=apex_art.build_style_block(look) if look else None
    if style: tl["style"]=style
    return tl

# ===================== RENDER ENGINE =====================
RENDER_JS = r"""
function c01(x){return x<0?0:x>1?1:x;}
function lerp(a,b,u){return a+(b-a)*u;}
var E={lin:function(u){return u;},outQuad:function(u){return 1-(1-u)*(1-u);},inQuad:function(u){return u*u;},
 outCubic:function(u){return 1-Math.pow(1-u,3);},inOutCubic:function(u){return u<.5?4*u*u*u:1-Math.pow(-2*u+2,3)/2;},
 inOutSine:function(u){return -(Math.cos(Math.PI*u)-1)/2;},
 outBack:function(u){var s=2.2;return 1+(s+1)*Math.pow(u-1,3)+s*Math.pow(u-1,2);},
 outExpo:function(u){return u>=1?1:1-Math.pow(2,-10*u);},inExpo:function(u){return u<=0?0:Math.pow(2,10*u-10);},
 outElastic:function(u){if(u===0||u===1)return u;var c=(2*Math.PI)/3;return Math.pow(2,-10*u)*Math.sin((u*10-0.75)*c)+1;},
 spring:function(u){return 1-Math.cos(u*Math.PI*1.6)*Math.exp(-u*4.2);}};
E.byName=function(n){return E[n]||E.outCubic;};
function q(s){return document.querySelector(s);}
function setO(s,v){var e=q(s);if(e)e.style.opacity=v;}
function ST(){return (window.TL&&TL.style)?TL.style:null;}
function getT(){var p=new URLSearchParams(location.search);var t=parseFloat(p.get('t'));
 if(isNaN(t)){var f=parseInt(p.get('f')||'0');t=f/(parseInt(p.get('fps')||'30'));}return t;}
function wrapWords(el){var kids=Array.prototype.slice.call(el.childNodes);el.innerHTML='';
 kids.forEach(function(node){
  if(node.nodeType===3){var parts=node.textContent.split(/(\s+)/);parts.forEach(function(p){
    if(p.trim()===''){el.appendChild(document.createTextNode(p));}
    else{var s=document.createElement('span');s.className='kw';s.textContent=p;el.appendChild(s);}});}
  else if(node.nodeName==='BR'){el.appendChild(node);}
  else{var s=document.createElement('span');s.className='kw';s.appendChild(node);el.appendChild(s);}});}
function kineticSplit(){var S=ST();if(!S||!S.kinetic)return;var m=S.kinetic.mode;
 if(m==='punch'||m==='none')return;var hh=document.querySelectorAll('.scene .hxl,.scene .hlg');
 for(var z=0;z<hh.length;z++)wrapWords(hh[z]);}
function applyTrans(el,kind,enter,exit,dir,ru,td){var op=(enter*(1-exit));
 if(kind==='push_slide'){el.style.filter='none';el.style.clipPath='none';el.style.opacity=op.toFixed(4);el.style.transform='translateX('+(dir*(1-enter)*70 - dir*exit*70).toFixed(1)+'px)';return;}
 if(kind==='scale_dissolve'){el.style.filter='none';el.style.clipPath='none';el.style.opacity=op.toFixed(4);el.style.transform='scale('+(lerp(0.88,1,enter)+exit*0.08).toFixed(3)+')';return;}
 if(kind==='blur_dissolve'){el.style.clipPath='none';el.style.opacity=op.toFixed(4);el.style.filter='blur('+(((1-enter)+exit)*9).toFixed(2)+'px)';el.style.transform='scale('+lerp(1.04,1,enter).toFixed(3)+')';return;}
 if(kind==='card_stack'){el.style.filter='none';el.style.clipPath='none';el.style.opacity=op.toFixed(4);el.style.transform='translateY('+((1-enter)*42 - exit*28).toFixed(1)+'px) rotate('+((1-enter)*-2.4 + exit*1.8).toFixed(2)+'deg) scale('+lerp(0.94,1,enter).toFixed(3)+')';return;}
 if(kind==='whip_pan'){var sk=(1-enter)*12 + exit*12;el.style.filter='none';el.style.clipPath='none';el.style.opacity=op.toFixed(4);el.style.transform='translateX('+(dir*(1-enter)*130 - dir*exit*130).toFixed(1)+'px) skewX('+(dir*sk).toFixed(1)+'deg)';return;}
 if(kind==='mask_wipe_h'){el.style.filter='none';el.style.transform='none';el.style.opacity=(op>0?1:0);el.style.clipPath='inset(0 '+(exit*100).toFixed(1)+'% 0 '+((1-enter)*100).toFixed(1)+'%)';return;}
 if(kind==='mask_wipe_v'){el.style.filter='none';el.style.opacity=(op>0?1:0);el.style.transform='translateY('+((1-enter)*14).toFixed(1)+'px)';el.style.clipPath='inset('+((1-enter)*100).toFixed(1)+'% 0 '+(exit*100).toFixed(1)+'% 0)';return;}
 if(kind==='mask_wipe_diag'){el.style.filter='none';el.style.transform='none';el.style.opacity=(op>0?1:0);var w=enter*150-25;el.style.clipPath='polygon(0 0,'+w.toFixed(0)+'% 0,'+(w-40).toFixed(0)+'% 100%,0 100%)';return;}
 /* fade_clip = original */
 el.style.filter='none';el.style.opacity=op.toFixed(4);
 el.style.clipPath='inset('+(exit*100).toFixed(2)+'% 0 '+((1-enter)*100).toFixed(2)+'% 0)';
 el.style.transform='translateY('+((1-E.outBack(c01(ru)))*26).toFixed(2)+'px)';}
function render(t){
 var S=ST();
 var eEnter=S?E.byName(S.ease.enter):E.outCubic, eExit=S?E.byName(S.ease.exit):E.inQuad, ePunch=S?E.byName(S.ease.punch):E.outBack;
 var camZ=S?S.cam.zoom:0.05, camP=S?S.cam.pan:10, PAR=S?S.parallax:0.45;
 var WD=S?S.world:{rings_rot:1.1,particle_seed:1.7,blob_amp:18,beam_sweep:0.05,grid_drift:10,mesh_amp:8};
 var intro=E.outCubic(c01(t/0.55));
 setO('.kicker',intro);setO('.guides',intro);setO('.brwrap',intro);setO('.hud',intro);setO('.ticks',intro);setO('.idxnum',intro);setO('.rulewrap',intro);setO('.radar',intro);
 var sb=q('.splitbar'); if(sb)sb.style.transform='scaleX('+E.outBack(c01(t/0.6))+')';
 setO('.lockup',E.outCubic(c01((t-0.25)/0.55)));
 var pb=q('.pbar'); if(pb)pb.style.width=(c01(t/TL.total)*100)+'%';
 var aI=-1,aP=0,camS=1,panX=0;
 for(var i=0;i<TL.scenes.length;i++){var s=TL.scenes[i];var lo=t-s.start,ln=s.end-s.start;
   if(lo>=-0.32&&lo<=ln+0.05){aI=i;aP=c01(lo/ln);camS=1+camZ*E.inOutSine(aP);panX=lerp(-camP,camP,E.inOutSine(aP));}}
 var st=q('.stage'); if(st)st.style.transform='translateX('+panX+'px) scale('+camS+')';
 var mesh=q('.mesh'); if(mesh)mesh.style.transform='translate('+(panX*-PAR+Math.sin(t*0.18)*WD.mesh_amp)+'px,'+(Math.cos(t*0.13)*(WD.mesh_amp*0.75))+'px)';
 var glow=q('.glow'); if(glow)glow.style.transform='scale('+(1+0.02*Math.sin(t*0.5))+')';
 var rings=q('.rings'); if(rings)rings.style.transform='translate(calc(-50% + '+(panX*-PAR*0.7)+'px),-50%) rotate('+(t*WD.rings_rot)+'deg)';
 var beam=q('.beam'); if(beam)beam.style.transform='translateX(-50%) rotate('+(18+Math.sin(t*(WD.beam_sweep||0.05)*6.28)*5)+'deg)';
 var blobs=document.querySelectorAll('.blob');
 for(var bi=0;bi<blobs.length;bi++){var bp=bi*2.1;blobs[bi].style.transform='translate(calc(-50% + '+(Math.sin(t*0.12+bp)*(WD.blob_amp||16))+'px),calc(-50% + '+(Math.cos(t*0.1+bp)*(WD.blob_amp||16))+'px))';}
 var grid=q('.grid'); if(grid)grid.style.transform='translate('+(panX*-PAR*0.5)+'px,'+(((t*(WD.grid_drift||10))%80))+'px)';
 var ps=document.querySelectorAll('.particle');var psd=WD.particle_seed||1.7;
 for(var k=0;k<ps.length;k++){var ph=k*psd;ps[k].style.transform='translate('+(Math.sin(t*0.5+ph)*26)+'px,'+(Math.cos(t*0.37+ph)*30)+'px)';}
 var km=S?S.kinetic:null;
 for(var i=0;i<TL.scenes.length;i++){
   var s=TL.scenes[i],el=document.getElementById(s.id);if(!el)continue;
   var lo=t-s.start,ln=s.end-s.start;
   if(lo< -0.32||lo> ln+0.05){el.style.display='none';continue;}
   el.style.display='flex';
   var ed=s.enter||0.6, td=(S?S.trans_dur:0.45), ru=c01(lo/ed);
   var enter=eEnter(ru), exit=eExit(c01((lo-(ln-td))/td));
   applyTrans(el, s.trans||'fade_clip', enter, exit, s.dir||1, ru, td);
   if(km&&km.mode&&km.mode!=='punch'&&km.mode!=='none'){
     var kws=el.querySelectorAll('.kw');
     for(var w2=0;w2<kws.length;w2++){var dd=0.12+w2*km.unit_stagger;var cu=eEnter(c01((lo-dd)/0.5));
       kws[w2].style.opacity=cu.toFixed(3);kws[w2].style.transform='translateY('+((1-cu)*km.unit_y).toFixed(2)+'px)';
       if(km.mode==='word_blur')kws[w2].style.filter='blur('+((1-cu)*km.unit_blur).toFixed(2)+'px)';
       else if(km.mode==='block_mask')kws[w2].style.clipPath='inset('+((1-cu)*100).toFixed(1)+'% 0 0 0)';}
   } else {
     var sg=el.querySelectorAll('.stag');
     for(var j=0;j<sg.length;j++){var d=0.16+j*(s.stag||0.10);var cu=E.outCubic(c01((lo-d)/0.5));sg[j].style.opacity=cu.toFixed(4);sg[j].style.transform='translateY('+((1-cu)*18).toFixed(2)+'px)';}
   }
   var pn=el.querySelectorAll('.punch');
   for(var m=0;m<pn.length;m++){var at=parseFloat(pn[m].getAttribute('data-at')||'0.3');var raw=(lo-at)/0.55;var pu=raw<=0?0:ePunch(c01(raw));var po=c01((lo-at)/0.16);var pre=(raw>-0.15&&raw<0)?(-0.04*(1-c01((raw+0.15)/0.15))):0;pn[m].style.transform='scale('+(lerp(0.55,1,pu)+pre).toFixed(3)+')';pn[m].style.opacity=po.toFixed(3);}
   var sw=el.querySelector('.sweep'),head=el.querySelector('.hxl,.hlg');
   if(head){if(!sw){sw=document.createElement('div');sw.className='sweep';head.appendChild(sw);}var swu=(lo-0.40)/0.5;if(swu>0&&swu<1){sw.style.opacity='1';sw.style.transform='translateX('+lerp(-140,240,swu)+'%) skewX(-18deg)';}else{sw.style.opacity='0';}}
   var dv=el.querySelector('.divider'); if(dv)dv.style.transform='scaleY('+E.outCubic(c01((lo-0.3)/0.6)).toFixed(3)+')';
 }
 if(window.motifSet){ if(aI>=0) motifSet(aI,aP); else {var mw=document.getElementById('motif'); if(mw)mw.style.opacity=0;} }
}
"""

def build_anim_html(aspect, concept, tl):
    A=ASPECTS[aspect]; W,H=A["w"],A["h"]
    look=concept.get("look"); theme=(look["theme"] if look else THEME)
    P=apex_art.palette_for(look, theme) if look else pack.PALETTES[THEME]
    scene_divs="\n".join(f'<div class="scene" id="s{i+1}">{html}</div>' for i,html in enumerate(concept["scenes"]))
    motif_svg=concept["motif_svg"](P)
    motif_js=concept.get("motif_js","")
    layers_html=apex_art.world_html(look, theme, W, H, None) if look else ""
    layers_css=apex_art.world_css(look, theme, W, H) if look else ""
    type_over=apex_art.type_css(look) if look else ""
    style=f"""
@page{{margin:0}} *{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;height:{H}px}}
body{{font-family:'Segoe UI','Inter',Arial,sans-serif;background:{P['base']};color:{P['text_primary']};-webkit-font-smoothing:antialiased;overflow:hidden}}
.canvas{{position:relative;width:{W}px;height:{H}px;background:{P['bg_grad']};overflow:hidden}}
.motif{{position:absolute;left:50%;top:{A['motif_top']}px;transform:translateX(-50%);z-index:3;opacity:0;will-change:transform,opacity}}
.head{{position:absolute;top:{A['safe_top']+44}px;left:0;right:0;display:flex;flex-direction:column;align-items:center;gap:13px;z-index:4}}
.kicker{{font-size:16px;font-weight:700;letter-spacing:5px;color:{P['text_tertiary']};text-transform:uppercase}}
.splitbar{{display:flex;width:130px;height:4px;border-radius:3px;overflow:hidden;transform-origin:center}}
.splitbar .n{{flex:1;background:{P['neutral']}}} .splitbar .a{{flex:1;background:{P['amber']};box-shadow:{P['lane_glow']}}}
.stage{{position:absolute;left:64px;right:64px;top:{H*0.31:.0f}px;height:{H*0.42:.0f}px;z-index:3;transform-origin:50% 45%}}
.scene{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;will-change:transform,opacity,clip-path}}
.hxl{{position:relative;font-size:{A['title']}px;font-weight:800;line-height:1.02;letter-spacing:-2px;color:{P['text_primary']};overflow:visible}}
.hlg{{position:relative;font-size:{A['lg']}px;font-weight:800;line-height:1.06;letter-spacing:-1.2px;color:{P['text_primary']};overflow:visible}}
.kw{{display:inline-block;will-change:transform,opacity}}
.punch{{display:inline-block;transform-origin:center bottom;color:{P['amber']}}}
.sweep{{position:absolute;top:0;bottom:0;left:0;width:42%;opacity:0;background:linear-gradient(100deg,transparent,rgba(255,255,255,.30),transparent);pointer-events:none}}
.sub{{margin-top:24px;font-size:{A['sub']}px;font-weight:400;line-height:1.45;color:{P['text_secondary']};max-width:840px}}
.tag{{font-size:16px;font-weight:800;letter-spacing:3px;text-transform:uppercase;color:{P['amber']};margin-bottom:22px}}
.split{{margin-top:42px;display:grid;grid-template-columns:1fr 1px 1fr;width:92%;max-width:840px}}
.divider{{background:{P['hairline']};transform-origin:top}}
.col{{padding:0 30px;display:flex;flex-direction:column;align-items:center}}
.lab{{font-size:26px;font-weight:800;letter-spacing:1px;color:{P['text_primary']};text-transform:uppercase}}
.lab .dot{{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:middle;margin-right:9px}}
.lab .dn{{background:{P['neutral']}}} .lab .da{{background:{P['amber']}}}
.brand{{font-size:17px;font-weight:600;color:{P['text_secondary']};margin-top:9px}}
.chips{{margin-top:18px;display:flex;gap:10px;flex-wrap:wrap;justify-content:center}}
.chip{{font-size:16px;font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:12px 18px;border-radius:5px;border:1px solid {P['hairline']}}}
.chip.n{{border-color:{P['chip_b_border']};color:{P['chip_b_text']}}} .chip.a{{border-color:{P['chip_g_border']};color:{P['chip_g_text']}}}
.ctabox{{margin-top:32px;font-size:{A['sub']}px;font-weight:600;line-height:1.45;color:{P['text_secondary']};max-width:780px}} .ctabox b{{color:{P['text_primary']};font-weight:800}}
.foot{{position:absolute;left:0;right:0;bottom:{A['safe_bottom']+40}px;display:flex;flex-direction:column;align-items:center;gap:22px;z-index:4}}
.lockup{{display:flex;align-items:center;justify-content:center;gap:18px}}
.bm{{display:flex;align-items:center;gap:14px}} .bm img{{display:block}}
.bname{{font-size:19px;font-weight:800;letter-spacing:1.5px;color:{P['text_primary']};text-transform:uppercase}}
.xsep{{font-size:17px;color:{P['text_tertiary']};font-weight:600}}
.pwrap{{width:240px;height:3px;background:{P['meter_track']};border-radius:3px;overflow:hidden}} .pbar{{height:100%;width:0%;background:{P['qbar']}}}
{layers_css}
{type_over}
"""
    body=f"""
<div class="canvas">
  {layers_html}
  <div class="motif" id="motif">{motif_svg}</div>
  <div class="head"><div class="kicker">{concept['kicker']}</div><div class="splitbar"><span class="n"></span><span class="a"></span></div></div>
  <div class="stage">{scene_divs}</div>
  <div class="foot"><div class="pwrap"><div class="pbar"></div></div>
    <div class="lockup">
      <div class="bm"><img src="{P['logo_arrow']}" height="30" alt=""><span class="bname">Apex IT Solutions</span></div>
      <span class="xsep">&times;</span>
      <div class="bm"><span class="bname">Apex Marketings</span><img src="{P['logo_m']}" height="36" alt=""></div>
    </div></div>
</div>
<script>var TL={json.dumps(tl)};var MS={json.dumps(concept.get("motif_scenes",[]))};{RENDER_JS}{motif_js}kineticSplit();render(getT());</script>
"""
    return pack.inject(f"<!doctype html><html><head><meta charset='utf-8'><style>{style}</style></head><body>{body}</body></html>")

# ===================== CAPTURE / ENCODE =====================
def _theme_base(concept):
    look=concept.get("look"); theme=look["theme"] if look else THEME
    return apex_art.palette_for(look, theme)["base"] if look else pack.PALETTES[THEME]["base"]

def _shot(html_path, aspect, t, out_png, base=None):
    A=ASPECTS[aspect]; raw=out_png+".raw.png"
    if base is None: base=pack.PALETTES[THEME]["base"]
    url="file:///"+html_path.replace("\\","/")+f"?t={t:.5f}"
    subprocess.run([CHROME,"--headless","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=2",
        "--default-background-color=00000000",f"--window-size={A['w']},{A['h']}",f"--screenshot={raw}",url],
        check=True, capture_output=True)
    img=Image.open(raw).convert("RGBA"); bg=Image.new("RGBA",img.size,pack.hex_rgb(base)+(255,))
    img=Image.alpha_composite(bg,img).convert("RGB")
    if img.size!=(A["w"],A["h"]): img=img.resize((A["w"],A["h"]),Image.LANCZOS)
    img.save(out_png,"PNG"); os.remove(raw)

def capture_frames(aspect, concept, tl, fdir):
    os.makedirs(fdir, exist_ok=True)
    html=os.path.join(TMP,f"anim_{aspect}.html")
    with open(html,"w",encoding="utf-8") as f: f.write(build_anim_html(aspect, concept, tl))
    base=_theme_base(concept); n=int(round(tl["total"]*FPS))
    for f in range(n):
        _shot(html, aspect, f/FPS, os.path.join(fdir,f"frame_{f:05d}.png"), base)
        if f%30==0 or f==n-1: print(f"  [{aspect}] {f+1}/{n}", flush=True)
    return n

def encode(aspect, fdir, audio):
    A=ASPECTS[aspect]; out=os.path.join(VIDEO_DIR,A["out"])
    subprocess.run([FF,"-y","-framerate",str(FPS),"-i",os.path.join(fdir,"frame_%05d.png"),"-i",audio,
        "-map","0:v:0","-map","1:a:0","-c:v","libx264","-pix_fmt","yuv420p","-crf","18","-preset","slow",
        "-vf",f"scale={A['w']}:{A['h']}:flags=lanczos,format=yuv420p","-r",str(FPS),
        "-c:a","aac","-b:a","192k","-ar",str(SR),"-movflags","+faststart","-shortest",out], check=True, capture_output=True)
    return out
def probe(mp4): return subprocess.run([FF,"-i",mp4], capture_output=True, text=True).stderr

# ===================== AUDIO BUILD (VO + music + SFX, ducked) =====================
def build_audio(concept):
    clips=[synth_line(text, sp) for (text, sp) in concept["narration"]]
    durs=[len(c)/SR for c in clips]
    tl=build_timeline(durs, concept.get("look"))
    # VO track
    n=int(tl["total"]*SR)+SR; vo=np.zeros(n,np.float32)
    for s,clip in zip(tl["scenes"],clips):
        i=int(s["vo_at"]*SR); j=min(n,i+len(clip)); vo[i:j]+=clip[:j-i]
    vo=vo/(np.max(np.abs(vo))+1e-9)*0.95
    write_wav(os.path.join(TMP,"vo_raw.wav"), vo[:int(tl["total"]*SR)])
    af="highpass=f=85,lowpass=f=13500,acompressor=threshold=-18dB:ratio=3:attack=8:release=120:makeup=2,treble=g=2:f=8000,aecho=0.8:0.85:14:0.04"
    subprocess.run([FF,"-y","-i",os.path.join(TMP,"vo_raw.wav"),"-af",af,"-ar",str(SR),os.path.join(TMP,"vo.wav")],check=True,capture_output=True)
    # music + sfx
    write_wav(os.path.join(TMP,"music.wav"), make_music(concept["music_mood"], tl["total"]))
    build_sfx(tl, os.path.join(TMP,"sfx.wav"))
    # mix: duck music + sfx under VO -> loudnorm -14
    fc=("[1:a]volume=0.5[mv];[mv][0:a]sidechaincompress=threshold=0.045:ratio=8:attack=20:release=320[md];"
        "[2:a][0:a]sidechaincompress=threshold=0.06:ratio=5:attack=15:release=240[sd];"
        "[0:a][md][sd]amix=inputs=3:normalize=0[mx];[mx]loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    mixp=os.path.join(TMP,"mix.wav")
    subprocess.run([FF,"-y","-i",os.path.join(TMP,"vo.wav"),"-i",os.path.join(TMP,"music.wav"),"-i",os.path.join(TMP,"sfx.wav"),
        "-filter_complex",fc,"-map","[a]","-ar",str(SR),mixp],check=True,capture_output=True)
    return tl, mixp

# ===================== MAIN =====================
def smoke():
    os.makedirs(TMP, exist_ok=True); concept=get_concept()
    tl, audio=build_audio(concept); base=_theme_base(concept)
    lk=concept.get("look", {})
    print("concept=%s look=%s/%s total=%.2fs"%(concept["id"], lk.get("lookbook","-"), lk.get("theme","-"), tl["total"]), flush=True)
    shutil.copy(audio, os.path.join(ROOT,"_audio_preview.wav"))
    html=os.path.join(TMP,"anim_smoke.html")
    with open(html,"w",encoding="utf-8") as f: f.write(build_anim_html("instagram", concept, tl))
    for s in tl["scenes"]:
        t=(s["start"]+s["end"])/2; _shot(html,"instagram",t,os.path.join(ROOT,f"_smoke_{s['id']}.png"), base); print("smoke",s["id"],round(t,2),flush=True)

def main():
    os.makedirs(VIDEO_DIR, exist_ok=True); concept=get_concept()
    tl, audio=build_audio(concept); print("concept=%s total=%.2fs"%(concept["id"],tl["total"]), flush=True)
    for aspect in ("instagram","linkedin"):
        fdir=os.path.join(TMP,f"frames_{aspect}")
        if os.path.isdir(fdir): shutil.rmtree(fdir)
        capture_frames(aspect, concept, tl, fdir)
        out=encode(aspect, fdir, audio); info=probe(out); import re
        v=re.search(r"Video: (\w+).*?(\d{3,4}x\d{3,4}).*?([\d.]+) fps", info, re.S); a=re.search(r"Audio: (\w+).*?(\d+) Hz", info, re.S)
        print(f"  {aspect}: {os.path.getsize(out)//1024}KB | {v.group(1) if v else '?'} {v.group(2) if v else '?'} {v.group(3) if v else '?'}fps | {a.group(1) if a else '?'} {a.group(2) if a else '?'}Hz", flush=True)
        shutil.rmtree(fdir)
    open(os.path.join(OUT,"video.md"),"w",encoding="utf-8").write(concept["caption"]+"\n")
    pack.KEEP_DIRS=set(pack.KEEP_DIRS)|{"video"}
    print("DONE. video/ holds:", sorted(os.listdir(VIDEO_DIR)), flush=True)

if __name__=="__main__":
    (smoke if (len(sys.argv)>1 and sys.argv[1]=="smoke") else main)()
