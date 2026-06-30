# -*- coding: utf-8 -*-
"""
apex_studio.py — Apex Studio: a local, no-IDE GUI for the daily image+video system.

Run:  python apex_studio.py   (or double-click run_studio.bat)  -> opens http://127.0.0.1:5000

Workflow: click "Copy GPT Prompt" -> paste it into GPT (Pro) -> paste the JSON it returns
here -> Validate -> Generate Image / Video / Both. Rendering is fully offline + free.
Optional: paste an API key to let the GUI call the LLM itself; or use a plain brief template.
"""
import json, os, queue, re, sys, threading, uuid, webbrowser
from flask import Flask, request, Response, jsonify, send_from_directory
import apex_spec
import apex_art

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "generated_images")
SPEC_PATH = os.path.join(ROOT, "day_spec.json")
PROMPT_FILE = os.path.join(ROOT, "GPT_PROMPT.md")
EXAMPLE = os.path.join(ROOT, "day_spec.example.json")
app = Flask(__name__)
JOBS = {}

# ---------------- generation jobs (subprocess + SSE) ----------------
def _run(job_id, cmds):
    j = JOBS[job_id]; env = dict(os.environ, APEX_SPEC=SPEC_PATH, PYTHONUNBUFFERED="1")
    try:
        for cmd in cmds:
            j["q"].put({"line": "$ " + " ".join(os.path.basename(c) for c in cmd)})
            import subprocess
            p = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True, bufsize=1)
            j["proc"] = p
            for line in p.stdout:
                j["q"].put({"line": line.rstrip()})
            p.wait()
            if p.returncode != 0:
                j["q"].put({"line": f"[exit {p.returncode}]"}); j["status"] = "error"; break
        else:
            j["status"] = "done"
    except Exception as ex:
        j["q"].put({"line": "ERROR: " + str(ex)}); j["status"] = "error"
    j["q"].put({"done": True, "status": j["status"]})

@app.post("/api/generate")
def api_generate():
    d = request.get_json(force=True); mode = d.get("mode", "both"); spec = d.get("spec")
    if any(j.get("status") == "running" for j in JOBS.values()):
        return jsonify({"ok": False, "errors": ["A job is already running — let it finish first."]}), 409
    if isinstance(spec, str):
        try: spec = json.loads(spec)
        except Exception as ex: return jsonify({"ok": False, "errors": ["JSON parse error: " + str(ex)]}), 400
    ok, errs = apex_spec.validate(spec)
    if not ok: return jsonify({"ok": False, "errors": errs}), 400
    # optional overrides
    ov = d.get("overrides", {})
    if ov.get("theme") and spec.get("carousel") is not None: spec["theme"] = ov["theme"]
    if ov.get("music_mood") and spec.get("video"): spec["video"]["music_mood"] = ov["music_mood"]
    with open(SPEC_PATH, "w", encoding="utf-8") as f: json.dump(spec, f, ensure_ascii=False, indent=2)
    py = sys.executable; cmds = []
    if mode in ("image", "both") and spec.get("carousel"): cmds.append([py, os.path.join(ROOT, "build_today_pack.py")])
    if mode in ("video", "both") and spec.get("video"):
        vargs = [py, os.path.join(ROOT, "build_today_video.py" if d.get("video_smoke") else "fast_render.py")]
        if d.get("video_smoke"): vargs.append("smoke")
        cmds.append(vargs)
    if not cmds: return jsonify({"ok": False, "errors": ["nothing to generate for this mode/spec"]}), 400
    jid = uuid.uuid4().hex[:8]; JOBS[jid] = {"q": queue.Queue(), "status": "running", "proc": None}
    threading.Thread(target=_run, args=(jid, cmds), daemon=True).start()
    return jsonify({"ok": True, "job": jid})

@app.get("/api/stream/<jid>")
def api_stream(jid):
    j = JOBS.get(jid)
    if not j: return "no job", 404
    def gen():
        yield "retry: 3000\n\n"
        while True:
            try: msg = j["q"].get(timeout=20)
            except queue.Empty: yield ": ping\n\n"; continue
            yield "data: " + json.dumps(msg) + "\n\n"
            if msg.get("done"): break
    return Response(gen(), mimetype="text/event-stream")

# ---------------- spec helpers ----------------
@app.post("/api/validate")
def api_validate():
    spec = request.get_json(force=True).get("spec")
    if isinstance(spec, str):
        try: spec = json.loads(spec)
        except Exception as ex: return jsonify({"ok": False, "errors": ["JSON parse error: " + str(ex)], "summary": {}})
    ok, errs = apex_spec.validate(spec); summ = {}
    if isinstance(spec, dict):
        if spec.get("carousel"): summ["carousel"] = {"kicker": spec["carousel"].get("kicker"), "slides": len(spec["carousel"].get("slides", []))}
        if spec.get("video"): summ["video"] = {"kicker": spec["video"].get("kicker"), "beats": len(spec["video"].get("scenes", [])), "motif": spec["video"].get("motif_name")}
        try:
            look = apex_art.choose_look(spec, kind="video")
            summ["art"] = {"look": look.get("lookbook"), "font": look.get("fonts", {}).get("name"),
                           "layout": look.get("layout", {}).get("template"),
                           "tone": look.get("grade", {}).get("tone"),
                           "d3": look.get("d3", {}).get("mode")}
        except Exception:
            pass
    return jsonify({"ok": ok, "errors": errs, "summary": summ})

@app.post("/api/assets/refresh")
def api_assets_refresh():
    try:
        import subprocess
        p = subprocess.run([sys.executable, os.path.join(ROOT, "fetch_assets.py")], cwd=ROOT,
                           capture_output=True, text=True, timeout=600)
        return jsonify({"ok": p.returncode == 0, "output": (p.stdout or "") + (p.stderr or "")})
    except Exception as ex:
        return jsonify({"ok": False, "output": str(ex)}), 500

@app.post("/api/test3d")
def api_test3d():
    try:
        import subprocess
        p = subprocess.run([sys.executable, os.path.join(ROOT, "fast_render.py"), "test3d"], cwd=ROOT,
                           capture_output=True, text=True, timeout=180)
        return jsonify({"ok": p.returncode == 0, "output": (p.stdout or "") + (p.stderr or "")})
    except Exception as ex:
        return jsonify({"ok": False, "output": str(ex)}), 500

@app.get("/api/prompt")
def api_prompt():
    topic = request.args.get("topic", "").strip()
    txt = open(PROMPT_FILE, encoding="utf-8").read() if os.path.exists(PROMPT_FILE) else "GPT_PROMPT.md is missing."
    if topic: txt += "\n\n---\nTODAY'S TOPIC (use this): " + topic + "\n"
    return Response(txt, mimetype="text/plain; charset=utf-8")

@app.get("/api/example")
def api_example():
    return Response(open(EXAMPLE, encoding="utf-8").read() if os.path.exists(EXAMPLE) else "{}", mimetype="application/json")

@app.post("/api/surprise")
def api_surprise():
    """Free, offline: generate a fresh random on-brand day_spec (random script + look)."""
    try:
        import apex_concept, datetime
        spec = apex_concept.generate(date=datetime.date.today().isoformat())
        with open(SPEC_PATH, "w", encoding="utf-8") as f: json.dump(spec, f, ensure_ascii=False, indent=2)
        return jsonify({"ok": True, "spec": spec})
    except Exception as ex:
        return jsonify({"ok": False, "error": str(ex)}), 500

@app.post("/api/llm")
def api_llm():
    import urllib.request
    d = request.get_json(force=True); prov = d.get("provider", "openai"); key = (d.get("key") or "").strip(); brief = d.get("brief", "")
    if not key: return jsonify({"ok": False, "error": "Paste an API key first."}), 400
    prompt = (open(PROMPT_FILE, encoding="utf-8").read() if os.path.exists(PROMPT_FILE) else "") + "\n\nTODAY'S TOPIC: " + brief + "\nReturn ONLY the JSON, no prose."
    try:
        if prov == "anthropic":
            body = json.dumps({"model": "claude-3-5-sonnet-latest", "max_tokens": 4096, "messages": [{"role": "user", "content": prompt}]}).encode()
            req = urllib.request.Request("https://api.anthropic.com/v1/messages", body, {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
            text = json.loads(urllib.request.urlopen(req, timeout=180).read())["content"][0]["text"]
        else:
            body = json.dumps({"model": "gpt-4o", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}).encode()
            req = urllib.request.Request("https://api.openai.com/v1/chat/completions", body, {"Authorization": "Bearer " + key, "content-type": "application/json"})
            text = json.loads(urllib.request.urlopen(req, timeout=180).read())["choices"][0]["message"]["content"]
        m = re.search(r"\{.*\}", text, re.S); spec = json.loads(m.group(0))
        return jsonify({"ok": True, "spec": spec})
    except Exception as ex:
        return jsonify({"ok": False, "error": str(ex)}), 500

@app.get("/api/outputs")
def api_outputs():
    res = {"carousel": {}, "video": [], "captions": {}}
    for dd in ["linkedin-dark", "linkedin-light", "fb-dark", "fb-light"]:
        p = os.path.join(OUT, dd)
        if os.path.isdir(p): res["carousel"][dd] = sorted(f for f in os.listdir(p) if f.endswith(".png"))
    vd = os.path.join(OUT, "video")
    if os.path.isdir(vd): res["video"] = sorted(f for f in os.listdir(vd) if f.endswith(".mp4"))
    for c in ["linkedin.md", "fb.md", "video.md"]:
        fp = os.path.join(OUT, c)
        if os.path.exists(fp): res["captions"][c] = open(fp, encoding="utf-8").read()
    return jsonify(res)

@app.get("/out/<path:p>")
def out(p):
    r = send_from_directory(OUT, p); r.headers["Cache-Control"] = "no-store"; return r

@app.post("/api/open")
def api_open():
    try: os.startfile(OUT)
    except Exception as ex: return jsonify({"ok": False, "error": str(ex)})
    return jsonify({"ok": True})

@app.get("/")
def index():
    return Response(PAGE, mimetype="text/html")

PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Apex Studio</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',Inter,Arial,sans-serif;background:linear-gradient(168deg,#16171b,#141417 46%,#101218);color:#ECEDF0;min-height:100vh;padding:28px}
.wrap{max-width:1180px;margin:0 auto}
h1{font-size:30px;letter-spacing:-1px}.muted{color:#9398A2}.amber{color:#FFBE0B}
.head{display:flex;align-items:center;gap:14px;margin-bottom:6px}
.bar{width:9px;height:30px;border-radius:3px;background:linear-gradient(#ECEDF0,#FFBE0B)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:22px}
.card{background:#1a1b20;border:1px solid #2a2b31;border-radius:14px;padding:18px}
.card h2{font-size:13px;letter-spacing:3px;text-transform:uppercase;color:#9398A2;margin-bottom:14px}
textarea{width:100%;min-height:230px;background:#0f1014;border:1px solid #2a2b31;border-radius:10px;color:#ECEDF0;padding:12px;font-family:Consolas,monospace;font-size:12.5px;resize:vertical}
input,select{background:#0f1014;border:1px solid #2a2b31;border-radius:8px;color:#ECEDF0;padding:9px 11px;font-size:13px}
input{width:100%}
button{cursor:pointer;border:0;border-radius:9px;padding:11px 16px;font-weight:700;font-size:13px;letter-spacing:.3px}
.btn{background:#23242b;color:#ECEDF0;border:1px solid #34353c}
.btn:hover{background:#2c2d35}
.amberbtn{background:#FFBE0B;color:#15161A}.amberbtn:hover{filter:brightness(1.06)}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.tabs{display:flex;gap:8px;margin-bottom:12px}
.tab{padding:8px 12px;border-radius:8px;background:#23242b;border:1px solid #34353c;font-size:12px;cursor:pointer}
.tab.on{background:#FFBE0B;color:#15161A;border-color:#FFBE0B}
.hide{display:none}
.ok{color:#7CFFB0}.err{color:#FF8A8A}
#log{background:#0c0d10;border:1px solid #2a2b31;border-radius:10px;padding:12px;height:180px;overflow:auto;font-family:Consolas,monospace;font-size:12px;white-space:pre-wrap;color:#AEB3BC}
.pbarwrap{height:8px;background:#23242b;border-radius:5px;overflow:hidden;margin:10px 0}
.pbar{height:100%;width:0;background:linear-gradient(90deg,#ECEDF0,#FFBE0B);transition:width .2s}
.thumbs{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.thumbs img{width:100%;border-radius:8px;border:1px solid #2a2b31}
video{width:100%;border-radius:10px;border:1px solid #2a2b31;background:#000}
.cap{background:#0f1014;border:1px solid #2a2b31;border-radius:8px;padding:10px;font-size:12px;color:#AEB3BC;white-space:pre-wrap;max-height:150px;overflow:auto;margin-top:8px}
small{color:#777e89}
.full{grid-column:1/3}
@media(max-width:820px){.grid{grid-template-columns:1fr}.full{grid-column:auto}.thumbs{grid-template-columns:repeat(2,1fr)}}
</style></head><body><div class="wrap">
<div class="head"><div class="bar"></div><h1>Apex <span class="amber">Studio</span></h1></div>
<div class="muted">Daily image + video posts — render <b>offline &amp; free</b>. Get the script from GPT, paste it, click generate.</div>

<div class="grid">
  <div class="card">
    <h2>1 · Get today's script</h2>
    <div class="row"><input id="topic" placeholder="(optional) today's topic / angle…"></div>
    <div class="row" style="margin-top:10px"><button class="amberbtn" onclick="copyPrompt()">Copy GPT Prompt</button>
      <button class="amberbtn" onclick="surprise()">✨ Surprise me (free)</button>
      <button class="btn" onclick="loadExample()">Load example JSON</button></div>
    <small>Paste the prompt into GPT (Pro). It returns a <b>day_spec JSON</b> — paste that on the right →</small>

    <div style="margin-top:16px" class="tabs">
      <div class="tab on" data-m="key" onclick="tab('key')">Optional: API key (1-click)</div>
      <div class="tab" data-m="brief" onclick="tab('brief')">Plain brief (template)</div>
    </div>
    <div id="m-key">
      <div class="row"><select id="prov"><option value="openai">OpenAI</option><option value="anthropic">Anthropic</option></select>
        <input id="key" placeholder="API key (stays local; blank = disabled)" style="flex:1"></div>
      <div class="row" style="margin-top:8px"><input id="brief" placeholder="brief / topic for the model…" style="flex:1">
        <button class="btn" onclick="llm()">Generate spec →</button></div>
      <small>Only this button uses the internet (your key). Everything else is offline.</small>
    </div>
    <div id="m-brief" class="hide">
      <div class="row"><input id="btopic" placeholder="topic…" style="flex:1"><button class="btn" onclick="briefTemplate()">Make template →</button></div>
      <small>Builds an editable JSON skeleton (no LLM). Fill the text in the box and Generate.</small>
    </div>
  </div>

  <div class="card">
    <h2>2 · Paste day_spec JSON</h2>
    <textarea id="spec" placeholder='Paste the JSON GPT returned here…'></textarea>
    <div class="row" style="margin-top:10px"><button class="btn" onclick="validate()">Validate</button>
      <span id="vres" class="muted"></span></div>
  </div>

  <div class="card full">
    <h2>3 · Generate</h2>
    <div class="row">
      <button class="amberbtn" onclick="gen('image')">Generate Image</button>
      <button class="amberbtn" onclick="gen('video')">Generate Video</button>
      <button class="amberbtn" onclick="gen('both')">Generate Both</button>
      <button class="btn" onclick="fastSmoke()">Fast smoke</button>
      <button class="btn" onclick="refreshAssets()">Refresh assets</button>
      <button class="btn" onclick="test3d()">3D gate</button>
      <span class="muted" style="margin-left:8px;font-size:12px">image ≈1 min · video uses fast renderer (live progress below)</span>
      <span style="flex:1"></span>
      <select id="ovtheme"><option value="">theme: spec</option><option value="dark">dark</option><option value="light">light</option></select>
      <select id="ovmood"><option value="">music: spec</option><option>driving</option><option>uplift</option><option>tense</option></select>
      <button class="btn" onclick="openFolder()">Open folder</button>
    </div>
    <div class="pbarwrap"><div class="pbar" id="pbar"></div></div>
    <div id="log"></div>
  </div>

  <div class="card full">
    <h2>4 · Preview</h2>
    <div class="row"><button class="btn" onclick="loadOutputs()">Refresh preview</button> <small id="ostat"></small></div>
    <div id="preview" style="margin-top:12px"></div>
  </div>
</div>
<script>
const $=s=>document.querySelector(s);
function tab(m){document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('on',t.dataset.m===m));$('#m-key').classList.toggle('hide',m!=='key');$('#m-brief').classList.toggle('hide',m!=='brief');}
async function copyPrompt(){const t=encodeURIComponent($('#topic').value||'');const r=await fetch('/api/prompt?topic='+t);const txt=await r.text();await navigator.clipboard.writeText(txt);toast('Prompt copied — paste it into GPT.');}
async function loadExample(){const r=await fetch('/api/example');$('#spec').value=JSON.stringify(await r.json(),null,2);validate();}
async function surprise(){toast('Generating a fresh concept…');const r=await fetch('/api/surprise',{method:'POST'});const j=await r.json();if(j.ok){$('#spec').value=JSON.stringify(j.spec,null,2);validate();toast('Fresh concept ready — Generate to render.');}else toast('Error: '+j.error);}
function getSpec(){try{return JSON.parse($('#spec').value)}catch(e){return $('#spec').value}}
async function validate(){const r=await fetch('/api/validate',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({spec:$('#spec').value})});const j=await r.json();const el=$('#vres');if(j.ok){el.className='ok';el.textContent='valid - '+JSON.stringify(j.summary);}else{el.className='err';el.textContent='x '+(j.errors||[]).join('; ');}return j.ok;}
async function llm(){const body={provider:$('#prov').value,key:$('#key').value,brief:$('#brief').value};toast('Calling model…');const r=await fetch('/api/llm',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});const j=await r.json();if(j.ok){$('#spec').value=JSON.stringify(j.spec,null,2);validate();toast('Spec generated.');}else toast('LLM error: '+j.error);}
function briefTemplate(){const t=$('#btopic').value||'your topic';const sk={id:t.toLowerCase().replace(/\W+/g,'_').slice(0,24),topic:t,theme:'dark',carousel:{kicker:'EDIT System',slides:[{motif:'A -> B',headline:['Hook line 1','**amber** line 2'],sub:'one short line'},{tag:'The problem',headline:['Problem line'],sub:'why it hurts',meter:{head:'',left:'',right:''}},{headline:['Reframe','the **insight**'],sub:'support'},{tag:'The fix',headline:['Fix it','then **scale**'],build_chips:['Apex IT thing','Apex IT thing'],growth_chips:['Apex Mktg thing','Apex Mktg thing']},{headline:['Payoff line'],sub:'in that order.',cta:'DM "AUDIT" — free.'}],linkedin:{caption:'LinkedIn caption…',hashtags:['#B2BMarketing','#WebDevelopment','#SEO']},fb:{caption:'FB caption…',hashtags:['#smallbusinesspakistan','#founders','#digitalmarketing']}},video:{kicker:'EDIT System',music_mood:'driving',motif_name:'none',motif_scenes:[],narration:[{text:'Line 1.',speed:1.0},{text:'Line 2.',speed:1.0},{text:'Line 3.',speed:1.0},{text:'Line 4.',speed:1.0},{text:'Line 5. Apex IT builds; Apex Marketings turns it into demand.',speed:1.0},{text:'DM AUDIT.',speed:1.0}],scenes:[{headline:['Hook','**amber**'],big:true},{tag:'Problem',headline:['Problem']},{headline:['Reframe','**insight**'],big:true},{headline:['So','**fix it**']},{tag:'The fix',headline:['Fix','**once**'],build_chips:['IT a','IT b'],growth_chips:['Mktg a','Mktg b']},{headline:['Payoff'],cta:'DM "AUDIT" — free.'}],caption:'Video caption…'}};$('#spec').value=JSON.stringify(sk,null,2);validate();}
let es=null;
async function gen(mode){if(!await validate())return;$('#log').textContent='';$('#pbar').style.width='0';
 const body={mode:mode,spec:$('#spec').value,overrides:{theme:$('#ovtheme').value,music_mood:$('#ovmood').value}};
 const r=await fetch('/api/generate',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});const j=await r.json();
 if(!j.ok){toast('✗ '+(j.errors||[]).join('; '));return;}
 let total=0,doneF=0;if(es)es.close();es=new EventSource('/api/stream/'+j.job);
 es.onmessage=e=>{const m=JSON.parse(e.data);if(m.line!=null){log(m.line);
   let mt=m.line.match(/\/(\d+)\b/);let mc=m.line.match(/\[(?:instagram|linkedin)\]\s+(\d+)\/(\d+)/);
   if(mc){doneF=+mc[1];total=+mc[2];$('#pbar').style.width=Math.min(100,doneF/total*100)+'%';}
   if(/wrote .*\//.test(m.line)){$('#pbar').dataset.s=(+$('#pbar').dataset.s||0)+25;$('#pbar').style.width=Math.min(100,+$('#pbar').dataset.s)+'%';}
 }if(m.done){es.close();$('#pbar').style.width='100%';toast('Done ('+m.status+')');loadOutputs();}};
}
async function fastSmoke(){if(!await validate())return;$('#log').textContent='';const body={mode:'video',spec:$('#spec').value,video_smoke:true,overrides:{theme:$('#ovtheme').value,music_mood:$('#ovmood').value}};const r=await fetch('/api/generate',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});const j=await r.json();if(!j.ok){toast('x '+(j.errors||[]).join('; '));return;}if(es)es.close();es=new EventSource('/api/stream/'+j.job);es.onmessage=e=>{const m=JSON.parse(e.data);if(m.line!=null)log(m.line);if(m.done){es.close();toast('Smoke '+m.status);loadOutputs();}};}
async function refreshAssets(){toast('Refreshing assets...');const r=await fetch('/api/assets/refresh',{method:'POST'});const j=await r.json();log((j.output||'').trim());toast(j.ok?'Assets ready':'Asset refresh failed');}
async function test3d(){toast('Running 3D gate...');const r=await fetch('/api/test3d',{method:'POST'});const j=await r.json();log((j.output||'').trim());toast(j.ok?'3D gate passed':'3D gate failed');}
function log(s){const l=$('#log');l.textContent+=s+'\n';l.scrollTop=l.scrollHeight;}
async function openFolder(){await fetch('/api/open',{method:'POST'});}
async function loadOutputs(){const r=await fetch('/api/outputs');const j=await r.json();const p=$('#preview');let h='';const b=Date.now();
 const folders=Object.keys(j.carousel||{});if(folders.length){h+='<div class="muted" style="margin:6px 0">Carousel</div>';for(const f of folders){h+='<div style="margin:4px 0 2px;font-size:12px" class="muted">'+f+'</div><div class="thumbs">';for(const im of j.carousel[f])h+='<img src="/out/'+f+'/'+im+'?b='+b+'">';h+='</div>';}}
 if((j.video||[]).length){h+='<div class="muted" style="margin:14px 0 6px">Video</div><div class="row">';for(const v of j.video)h+='<div style="flex:1;min-width:240px"><div class="muted" style="font-size:12px">'+v+'</div><video controls src="/out/video/'+v+'?b='+b+'"></video></div>';h+='</div>';}
 const caps=j.captions||{};for(const c in caps)h+='<div class="muted" style="margin:12px 0 4px;font-size:12px">'+c+'</div><div class="cap">'+caps[c].replace(/</g,'&lt;')+'</div>';
 p.innerHTML=h||'<span class="muted">No outputs yet — generate something.</span>';$('#ostat').textContent='refreshed';}
let tT;function toast(s){let t=$('#toast');if(!t){t=document.createElement('div');t.id='toast';t.style.cssText='position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#FFBE0B;color:#15161A;padding:10px 18px;border-radius:10px;font-weight:700;z-index:9';document.body.appendChild(t);}t.textContent=s;t.style.opacity=1;clearTimeout(tT);tT=setTimeout(()=>t.style.opacity=0,2600);}
loadOutputs();
</script></div></body></html>"""

if __name__ == "__main__":
    port = 5000
    try: threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    except Exception: pass
    print(f"Apex Studio -> http://127.0.0.1:{port}  (Ctrl+C to stop)")
    app.run(host="127.0.0.1", port=port, threaded=True)
