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
    if spec is None and os.environ.get("APEX_AUTO"):
        import apex_concept
        spec = apex_concept.generate()
        print("APEX_AUTO generated:", spec.get("id"), "| topic:", spec.get("topic"), flush=True)
    look = apex_art.choose_look(spec or {}, kind="video")
    if spec and spec.get("video"):
        print("APEX_SPEC video loaded:", spec.get("id", "?"), "| look:", look["lookbook"], look["theme"],
              "| seed:", look.get("seed"), "(pin in spec/APEX_SEED to reproduce)", flush=True)
        c = apex_spec.build_video_concept(spec, VC.MOTIFS, look=look)
    else:
        c = dict(VC.get_today())
    c["look"] = look
    c["raw_video"] = (spec.get("video") if (spec and spec.get("video")) else None)  # raw beats for apex_lush
    c["art"] = (spec or {}).get("art_direction")  # pinned art axes (anti-repeat); None => seed-derived
    # carousel captions so a video render keeps every platform .md file in sync with the concept
    if spec and spec.get("carousel"):
        try:
            c["li_caption"], c["fb_caption"] = apex_spec.carousel_captions(spec["carousel"])
        except Exception:
            pass
    return c

def write_captions(concept):
    """Keep all platform caption files in sync with the rendered video:
    video.md = video caption; linkedin.md / fb.md = carousel captions (when a day_spec is present)."""
    open(os.path.join(OUT, "video.md"), "w", encoding="utf-8").write((concept.get("caption", "") or "").rstrip() + "\n")
    if concept.get("li_caption"):
        open(os.path.join(OUT, "linkedin.md"), "w", encoding="utf-8").write(concept["li_caption"])
    if concept.get("fb_caption"):
        open(os.path.join(OUT, "fb.md"), "w", encoding="utf-8").write(concept["fb_caption"])

ROOT, OUT = pack.ROOT, pack.OUT
VIDEO_DIR = os.path.join(OUT, "video")
TMP = os.path.join(tempfile.gettempdir(), "apex_vid")
KDIR = os.path.join(ROOT, "assets", "kokoro")
FF = imageio_ffmpeg.get_ffmpeg_exe()
CHROME = pack.CHROME
FPS = int(os.environ.get("APEX_FPS", "30"))   # 30 default (+motion blur = cinematic); APEX_FPS=60 for max-smooth
SR, THEME = 48000, "dark"
VOICE = "af_heart"                      # warm, natural, engaging (kokoro v1.0)
VOICES = ["af_heart", "af_bella", "af_nicole", "am_michael", "bm_george", "am_onyx"]  # seeded variety
_CUR_VOICE = VOICE                      # set per-concept in build_audio
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
    try:
        s, sr = _kokoro().create(text, voice=_CUR_VOICE, speed=speed, lang="en-us")
    except Exception:   # any seeded voice not present -> safe fallback to the default
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

# ---- real audio assets (CC0 music beds + SFX) with procedural fallback ----
MUSIC_DIR = os.path.join(ROOT, "assets", "music")   # assets/music/{driving,uplift,tense}/*.mp3|wav
SFX_DIR = os.path.join(ROOT, "assets", "sfx")        # assets/sfx/{whoosh,riser,tick,chime,thud,impact}*.wav|mp3
def _load_audio(path):
    """Decode any audio file (mp3/wav/...) to mono float32 @ SR via ffmpeg. None on failure."""
    try:
        r = subprocess.run([FF, "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                           capture_output=True)
        if r.returncode != 0 or not r.stdout:
            return None
        a = np.frombuffer(r.stdout, dtype=np.float32).copy()
        return (a/(np.max(np.abs(a))+1e-9)).astype(np.float32)
    except Exception:
        return None
def _loop_match(sig, seconds):
    n = int(seconds*SR)
    if len(sig) >= n: return sig[:n].astype(np.float32)
    return np.tile(sig, n//len(sig)+1)[:n].astype(np.float32)
def get_music_bed(mood, seconds, seed=0):
    """Seeded pick from assets/music/<mood>/ (looped/trimmed to length); procedural fallback."""
    import glob
    files = sorted(glob.glob(os.path.join(MUSIC_DIR, mood, "*.mp3")) + glob.glob(os.path.join(MUSIC_DIR, mood, "*.wav")))
    if files:
        sig = _load_audio(files[int(seed) % len(files)])
        if sig is not None and len(sig) > SR:
            sig = _loop_match(sig, seconds)
            f = int(0.8*SR); sig[:f] *= np.linspace(0,1,f); sig[-f:] *= np.linspace(1,0,f)
            return sig.astype(np.float32)
    return make_music(mood, seconds)
def _real_sfx(name):
    import glob
    for ext in ("wav", "mp3"):
        fs = sorted(glob.glob(os.path.join(SFX_DIR, name + "*." + ext)))
        if fs:
            sig = _load_audio(fs[0])
            if sig is not None and len(sig) > 100:
                return (sig*0.7).astype(np.float32)
    return None

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
        if name not in cache:
            r=_real_sfx(name); cache[name]=r if r is not None else SFX[name]()   # real file else procedural
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
function wrapChars(el){var kids=Array.prototype.slice.call(el.childNodes);el.innerHTML='';
 kids.forEach(function(node){
  if(node.nodeType===3){var chars=node.textContent.split('');chars.forEach(function(ch){
    if(ch==='\n'){return;} if(ch===' '){el.appendChild(document.createTextNode(' '));}
    else{var s=document.createElement('span');s.className='kw ch';s.textContent=ch;el.appendChild(s);}});}
  else if(node.nodeName==='BR'){el.appendChild(node);}
  else{var s=document.createElement('span');s.className='kw ch';s.appendChild(node);el.appendChild(s);}});}
function kineticSplit(){var S=ST();if(!S||!S.kinetic)return;var m=S.kinetic.mode;
 if(m==='punch'||m==='none')return;var hh=document.querySelectorAll('.scene .hxl,.scene .hlg');
 for(var z=0;z<hh.length;z++){if(m==='char_cascade'||m==='typewriter')wrapChars(hh[z]);else wrapWords(hh[z]);}}
function applyTrans(el,kind,enter,exit,dir,ru,td){var op=(enter*(1-exit));
 if(kind==='push_slide'){el.style.filter='none';el.style.clipPath='none';el.style.opacity=op.toFixed(4);el.style.transform='translateX('+(dir*(1-enter)*70 - dir*exit*70).toFixed(1)+'px)';return;}
 if(kind==='scale_dissolve'){el.style.filter='none';el.style.clipPath='none';el.style.opacity=op.toFixed(4);el.style.transform='scale('+(lerp(0.88,1,enter)+exit*0.08).toFixed(3)+')';return;}
 if(kind==='blur_dissolve'){el.style.clipPath='none';el.style.opacity=op.toFixed(4);el.style.filter='blur('+(((1-enter)+exit)*9).toFixed(2)+'px)';el.style.transform='scale('+lerp(1.04,1,enter).toFixed(3)+')';return;}
 if(kind==='card_stack'){el.style.filter='none';el.style.clipPath='none';el.style.opacity=op.toFixed(4);el.style.transform='translateY('+((1-enter)*42 - exit*28).toFixed(1)+'px) rotate('+((1-enter)*-2.4 + exit*1.8).toFixed(2)+'deg) scale('+lerp(0.94,1,enter).toFixed(3)+')';return;}
 if(kind==='whip_pan'){var sk=(1-enter)*12 + exit*12;el.style.filter='none';el.style.clipPath='none';el.style.opacity=op.toFixed(4);el.style.transform='translateX('+(dir*(1-enter)*130 - dir*exit*130).toFixed(1)+'px) skewX('+(dir*sk).toFixed(1)+'deg)';return;}
 if(kind==='mask_wipe_h'){el.style.filter='none';el.style.transform='none';el.style.opacity=(op>0?1:0);el.style.clipPath='inset(0 '+(exit*100).toFixed(1)+'% 0 '+((1-enter)*100).toFixed(1)+'%)';return;}
 if(kind==='mask_wipe_v'){el.style.filter='none';el.style.opacity=(op>0?1:0);el.style.transform='translateY('+((1-enter)*14).toFixed(1)+'px)';el.style.clipPath='inset('+((1-enter)*100).toFixed(1)+'% 0 '+(exit*100).toFixed(1)+'% 0)';return;}
 if(kind==='mask_wipe_diag'){el.style.filter='none';el.style.transform='none';el.style.opacity=(op>0?1:0);var w=enter*150-25;el.style.clipPath='polygon(0 0,'+w.toFixed(0)+'% 0,'+(w-40).toFixed(0)+'% 100%,0 100%)';return;}
 if(kind==='flip_3d'){el.style.clipPath='none';el.style.filter='none';el.style.opacity=op.toFixed(4);el.style.transform='rotateY('+((1-enter)*-70+exit*70).toFixed(2)+'deg) translateZ('+(enter*24).toFixed(1)+'px)';return;}
 if(kind==='cube_rotate'){el.style.clipPath='none';el.style.filter='none';el.style.opacity=op.toFixed(4);el.style.transform='rotateY('+(dir*((1-enter)*-90+exit*90)).toFixed(2)+'deg) translateX('+(dir*((1-enter)*60-exit*60)).toFixed(1)+'px)';return;}
 if(kind==='zoom_blur'){el.style.clipPath='none';el.style.opacity=op.toFixed(4);el.style.filter='blur('+(((1-enter)+exit)*13).toFixed(2)+'px)';el.style.transform='scale('+(lerp(1.18,1,enter)+exit*.16).toFixed(3)+')';return;}
 if(kind==='iris_wipe'){el.style.filter='none';el.style.transform='none';el.style.opacity=(op>0?1:0);var rr=(enter*(1-exit))*140;el.style.clipPath='circle('+rr.toFixed(1)+'% at 50% 50%)';return;}
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
 setO('.kicker',intro);setO('.guides',intro);setO('.brwrap',intro);setO('.hud',intro);setO('.ticks',intro);setO('.idxnum',intro);setO('.rulewrap',intro);setO('.radar',intro);setO('.furn',intro);setO('.world-set',intro);
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
 var D=S?S.d3:null;
 if(D&&D.mode&&D.mode!=='none'){
   var pr=q('#d3prism'); if(pr)pr.style.transform='translateZ(10px) rotateX('+(-16+Math.sin(t*0.25)*7).toFixed(2)+'deg) rotateY('+(t*(D.speed||0.2)*90).toFixed(2)+'deg)';
   var cs=document.querySelectorAll('#d3stack .d3-card');
   for(var ci=0;ci<cs.length;ci++){cs[ci].style.transform='translateZ('+((ci-1.5)*(D.depth||64)).toFixed(1)+'px) translateY('+(ci*26+Math.sin(t*.35+ci)*9).toFixed(1)+'px) translateX('+(Math.sin(t*.22+ci)*7).toFixed(1)+'px) rotateY('+(-15+Math.sin(t*.2)*6).toFixed(2)+'deg)';cs[ci].style.opacity=(0.55+ci*.12).toFixed(2);}
   var tw=document.querySelectorAll('#d3tower .d3-ring');
   for(var ti=0;ti<tw.length;ti++){var spin=t*(D.speed||0.2)*120;tw[ti].style.transform='translateY('+(ti*40-100).toFixed(1)+'px) translateZ('+(Math.sin(t*.5+ti*.6)*14).toFixed(1)+'px) rotateX(64deg) rotateZ('+(spin+ti*22).toFixed(1)+'deg)';tw[ti].style.opacity=(ti==5?0.95:(0.5+ti*0.05)).toFixed(2);}
   if(D.mode==='depth_parallax'){
     var dm=q('.mesh'); if(dm)dm.style.transform='translateZ(-260px) translate('+(panX*-2.0).toFixed(1)+'px,0) scale(1.4)';
     var dr=q('.rings'); if(dr)dr.style.transform='translate(calc(-50% + '+(panX*-1.4).toFixed(1)+'px),-50%) translateZ(-120px) rotate('+(t*WD.rings_rot).toFixed(2)+'deg)';
     var dg=q('.glow'); if(dg)dg.style.transform='translateZ(-340px) scale(1.6)';
   }
 }
 var ps=document.querySelectorAll('.particle');var psd=WD.particle_seed||1.7;
 for(var k=0;k<ps.length;k++){var ph=k*psd;ps[k].style.transform='translate('+(Math.sin(t*0.5+ph)*26)+'px,'+(Math.cos(t*0.37+ph)*30)+'px)';}
 var wsd=document.querySelectorAll('.world-set .wd');
 for(var wi=0;wi<wsd.length;wi++){var wph=wi*1.3;wsd[wi].style.transform='translate('+(Math.sin(t*0.16+wph)*14).toFixed(1)+'px,'+(Math.cos(t*0.13+wph)*12).toFixed(1)+'px)';}
 var eqb=document.querySelectorAll('.furn-eq span');
 for(var ei=0;ei<eqb.length;ei++){var ev=0.45+0.55*Math.abs(Math.sin(t*1.7+ei*0.55));eqb[ei].style.transformOrigin='bottom';eqb[ei].style.transform='scaleY('+ev.toFixed(2)+')';}
 var ctl=document.querySelectorAll('.ctile');
 for(var cl=0;cl<ctl.length;cl++){ctl[cl].style.transform='translateY('+(Math.sin(t*1.2+cl*0.9)*5).toFixed(1)+'px)';}
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
       if(km.mode==='typewriter'){cu=(w2<Math.floor(c01((lo-.12)/1.05)*(kws.length+1)))?1:0;}
       kws[w2].style.opacity=cu.toFixed(3);kws[w2].style.transform='translateY('+((1-cu)*km.unit_y).toFixed(2)+'px)';
       if(km.mode==='word_blur')kws[w2].style.filter='blur('+((1-cu)*km.unit_blur).toFixed(2)+'px)';
       else if(km.mode==='block_mask'||km.mode==='line_rise_serif')kws[w2].style.clipPath='inset('+((1-cu)*100).toFixed(1)+'% 0 0 0)';
       else if(km.mode==='char_cascade')kws[w2].style.transform='translateY('+((1-cu)*34).toFixed(2)+'px) rotateX('+((1-cu)*-55).toFixed(1)+'deg)';}
   } else {
     var sg=el.querySelectorAll('.stag');
     for(var j=0;j<sg.length;j++){var d=0.16+j*(s.stag||0.10);var cu=E.outCubic(c01((lo-d)/0.5));sg[j].style.opacity=cu.toFixed(4);sg[j].style.transform='translateY('+((1-cu)*18).toFixed(2)+'px)';}
   }
   var pn=el.querySelectorAll('.punch');
   for(var m=0;m<pn.length;m++){var at=parseFloat(pn[m].getAttribute('data-at')||'0.3');var raw=(lo-at)/0.55;var pu=raw<=0?0:ePunch(c01(raw));var po=c01((lo-at)/0.16);var pre=(raw>-0.15&&raw<0)?(-0.04*(1-c01((raw+0.15)/0.15))):0;pn[m].style.transform='scale('+(lerp(0.55,1,pu)+pre).toFixed(3)+')';pn[m].style.opacity=po.toFixed(3);}
   var sw=el.querySelector('.sweep'),head=el.querySelector('.hxl,.hlg');
   if(head){if(!sw){sw=document.createElement('div');sw.className='sweep';head.appendChild(sw);}var swu=(lo-0.40)/0.5;if(swu>0&&swu<1){sw.style.opacity='1';sw.style.transform='translateX('+lerp(-140,240,swu)+'%) skewX(-18deg)';}else{sw.style.opacity='0';}}
   var dv=el.querySelector('.divider'); if(dv)dv.style.transform='scaleY('+E.outCubic(c01((lo-0.3)/0.6)).toFixed(3)+')';
   var ics=el.querySelectorAll('.ic');
   for(var ii=0;ii<ics.length;ii++){var iu=E.outBack(c01((lo-0.18-ii*0.08)/0.45));ics[ii].style.opacity=c01(iu*1.2).toFixed(3);ics[ii].style.transform='translateY('+((1-iu)*14).toFixed(1)+'px) scale('+lerp(.74,1,iu).toFixed(3)+')';}
 }
 var aux=document.querySelectorAll('.motif-stage .aux');
 for(var ai=0;ai<aux.length;ai++){var au=(aI>=0)?E.outCubic(c01((aP-.1-ai*.08)/.7)):0;aux[ai].style.opacity=(.12+.5*au).toFixed(3);aux[ai].style.transform='translate(-50%,-50%) scale(calc(var(--ms) * '+(0.86+.16*au).toFixed(3)+')) rotate('+((t*10)+(ai*18)).toFixed(1)+'deg)';}
 if(window.motifSet){ if(aI>=0) motifSet(aI,aP); else {var mw=document.getElementById('motif'); if(mw)mw.style.opacity=0;} }
}
"""

def _furniture(A, P, kicker=""):
    """Persistent 'instrument' graphic furniture (grid + edge rulers + data rail + tags)
    so every scene has graphic density regardless of the spec. Static; fades in with intro."""
    W, H = A["w"], A["h"]; st, sb = A["safe_top"], A["safe_bottom"]
    tick = P["tick"]; hair = P["hairline"]; amber = P["amber"]
    r, g, b = pack.hex_rgb(P["text_primary"])
    L = []
    for i, x in enumerate(range(80, W - 60, 40)):
        h = 13 if i % 5 == 0 else 6
        L.append(f'<line x1="{x}" y1="{st+6}" x2="{x}" y2="{st+6+h}" stroke="{tick}" stroke-width="1"/>')
        L.append(f'<line x1="{x}" y1="{H-sb-6}" x2="{x}" y2="{H-sb-6-h}" stroke="{tick}" stroke-width="1"/>')
    railx = W - 46; y0, y1 = int(H * 0.32), int(H * 0.68)
    L.append(f'<line x1="{railx}" y1="{y0}" x2="{railx}" y2="{y1}" stroke="{hair}" stroke-width="1"/>')
    for j, y in enumerate(range(y0, y1, 34)):
        w = 13 if j % 3 == 0 else 7
        col = amber if j % 6 == 0 else tick
        L.append(f'<line x1="{railx-w}" y1="{y}" x2="{railx}" y2="{y}" stroke="{col}" stroke-width="1.5"/>')
    for cxp, cyp in ((0.5, 0.30), (0.80, 0.52), (0.22, 0.70)):  # instrument crosshair marks
        cx, cy, s = int(W * cxp), int(H * cyp), 8
        L.append(f'<line x1="{cx-s}" y1="{cy}" x2="{cx+s}" y2="{cy}" stroke="{tick}" stroke-width="1"/>')
        L.append(f'<line x1="{cx}" y1="{cy-s}" x2="{cx}" y2="{cy+s}" stroke="{tick}" stroke-width="1"/>')
    svg = f'<svg class="furn-svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(L)}</svg>'
    wm = (kicker or "APEX").upper()
    eq = "".join('<span style="height:%dpx"></span>' % h
                 for h in (12, 26, 16, 32, 20, 28, 14, 34, 18, 24, 22, 30, 16, 26, 12, 22))
    return (f'<div class="furn">'
            f'<div class="furn-eq">{eq}</div>'
            f'<div class="furn-grid" style="background-image:'
            f'linear-gradient(rgba({r},{g},{b},.075) 1px,transparent 1px),'
            f'linear-gradient(90deg,rgba({r},{g},{b},.075) 1px,transparent 1px)"></div>'
            f'{svg}'
            f'<div class="furn-wm">{wm}</div>'
            f'<div class="furn-tag bl">&#9679; SIGNAL // LIVE &middot; 2026</div>'
            f'</div>')

def build_anim_html(aspect, concept, tl):
    A=ASPECTS[aspect]; W,H=A["w"],A["h"]
    look=concept.get("look"); theme=(look["theme"] if look else THEME)
    P=apex_art.palette_for(look, theme) if look else pack.PALETTES[THEME]
    nr,ng,nb=pack.hex_rgb(P["text_primary"])
    scene_divs="\n".join(f'<div class="scene" id="s{i+1}">{html}</div>' for i,html in enumerate(concept["scenes"]))
    primary_motif=concept["motif_svg"](P)
    if concept.get("motif_layers"):
        layers=[f'<div class="motif-layer primary" data-layer="primary">{primary_motif}</div>']
        for j,layer in enumerate(concept.get("motif_layers", [])[:3]):
            try:
                svg=layer["motif_svg"](P)
            except Exception:
                continue
            left=layer.get("left", 50); top=layer.get("top", 50); scale=layer.get("scale", 0.72)
            layers.append(f'<div class="motif-layer aux aux{j}" data-layer="{layer.get("motif_name","aux")}" style="left:{left}%;top:{top}%;--ms:{scale}">{svg}</div>')
        motif_svg='<div class="motif-stage">'+"".join(layers)+"</div>"
    else:
        motif_svg=primary_motif
    motif_js=concept.get("motif_js","")
    layers_html=apex_art.world_html(look, theme, W, H, None) if look else ""
    layers_css=apex_art.world_css(look, theme, W, H) if look else ""
    font_css=apex_art.fontface_css(look) if look else ""
    layout_over=apex_art.layout_css(look, W, H, kind="video") if look else ""
    d3_css=apex_art.d3_css(look, theme) if look else ""
    d3_html=apex_art.d3_html(look, theme) if look else ""
    import apex_worlds
    ws_name=(look or {}).get("world_setpiece") if look else None
    worlds_html=apex_worlds.world_html(ws_name, P, W, H, (look or {}).get("seed", 0)) if ws_name else ""
    worlds_css=apex_worlds.world_css(P) if ws_name else ""
    import apex_icons
    icon_css=apex_icons.css(P)
    type_over=apex_art.type_css(look) if look else ""
    style=f"""
@page{{margin:0}} *{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;height:{H}px}}
{font_css}
body{{font-family:'Segoe UI','Inter',Arial,sans-serif;background:{P['base']};color:{P['text_primary']};-webkit-font-smoothing:antialiased;overflow:hidden}}
.canvas{{position:relative;width:{W}px;height:{H}px;background:{P['bg_grad']};overflow:hidden}}
.motif{{position:absolute;left:50%;top:{A['motif_top']}px;transform:translateX(-50%);z-index:2;opacity:0;will-change:transform,opacity}}
.motif-stage{{position:relative;width:460px;height:320px;transform-style:preserve-3d}}
.motif-stage>.motif-layer.primary{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:100%;height:100%}}
.motif-stage>.motif-layer.aux{{position:absolute;transform:translate(-50%,-50%) scale(var(--ms));opacity:.55;filter:blur(.1px) drop-shadow(0 22px 45px rgba(0,0,0,.24))}}
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
.furn{{position:absolute;inset:0;z-index:1;pointer-events:none}}
.furn-grid{{position:absolute;inset:0;background-size:96px 96px}}
.furn-svg{{position:absolute;inset:0}}
.furn-wm{{position:absolute;left:-58px;top:50%;transform:translateY(-50%) rotate(-90deg);transform-origin:center;
  font-size:15px;font-weight:800;letter-spacing:10px;color:{P['text_tertiary']};opacity:.55;text-transform:uppercase}}
.furn-tag{{position:absolute;font-size:13px;letter-spacing:3px;color:{P['text_tertiary']};font-weight:700;text-transform:uppercase}}
.furn-tag.bl{{right:58px;bottom:{A['safe_bottom']+34}px;font-size:11px;opacity:.7}}
.bgnum{{position:absolute;right:-10px;bottom:-70px;font-size:300px;font-weight:800;line-height:.78;
  letter-spacing:-14px;color:rgba({nr},{ng},{nb},.045);z-index:0;pointer-events:none;font-variant-numeric:tabular-nums}}
.furn-eq{{position:absolute;left:50%;bottom:{A['safe_bottom']+128}px;transform:translateX(-50%);display:flex;align-items:flex-end;gap:5px;height:36px;opacity:.55}}
.furn-eq span{{width:4px;background:{P['tick']};border-radius:2px}}
.furn-eq span:nth-child(4n){{background:{P['amber']}}}
{layers_css}
{worlds_css}
{icon_css}
{d3_css}
{type_over}
{layout_over}
"""
    body=f"""
<div class="canvas">
  {layers_html}
  {worlds_html}
  {_furniture(A, P, concept.get('kicker',''))}
  {d3_html}
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
    global _CUR_VOICE
    _seed=int((concept.get("look") or {}).get("seed", 0) or 0)
    _CUR_VOICE=VOICES[_seed % len(VOICES)]   # seeded voice variety (safe fallback in synth_line)
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
    write_wav(os.path.join(TMP,"music.wav"), get_music_bed(concept["music_mood"], tl["total"], _seed))
    build_sfx(tl, os.path.join(TMP,"sfx.wav"))
    # mix: duck music + sfx under VO -> loudnorm -14
    # music sits well UNDER the voiceover: lower bed level + stronger sidechain duck under VO.
    fc=("[1:a]volume=0.16[mv];[mv][0:a]sidechaincompress=threshold=0.02:ratio=16:attack=15:release=300[md];"
        "[2:a]volume=0.6[sx];[sx][0:a]sidechaincompress=threshold=0.05:ratio=6:attack=12:release=240[sd];"
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
    write_captions(concept)
    pack.KEEP_DIRS=set(pack.KEEP_DIRS)|{"video"}
    print("DONE. video/ holds:", sorted(os.listdir(VIDEO_DIR)), flush=True)

if __name__=="__main__":
    (smoke if (len(sys.argv)>1 and sys.argv[1]=="smoke") else main)()
