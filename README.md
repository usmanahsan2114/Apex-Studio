# Apex Studio

**A tiny local app that turns one JSON file into a daily, premium social-media post — a 5-slide image carousel *and* a ~35-second narrated vector-motion video — rendered 100% offline and free on your own PC.**

Built for two sister B2B brands, **Apex IT Solutions** (the *build* brand) and **Apex Marketings** (the *growth* brand). One co-branded post represents both: monochrome design with a single amber accent, the thesis *"Build the system. Turn it into demand."*

The only step that touches the internet is **your own** GPT (Pro) session, where you generate the day's script. Everything else — images, voiceover, music, sound design, video encoding — runs locally with no API costs.

---

## How it works (the daily workflow)

```
  ┌─────────────┐   copy prompt    ┌──────────────┐   paste day_spec.json   ┌──────────────┐
  │ Apex Studio │ ───────────────▶ │  GPT (Pro)   │ ──────────────────────▶ │ Apex Studio  │
  │  (browser)  │  (your topic)    │ researches + │      the day's spec     │  Validate ▶  │
  └─────────────┘                  │  writes JSON │                         │  Generate ▶  │
                                   └──────────────┘                         └──────┬───────┘
                                                                                   │ offline render
                                                                                   ▼
                                              generated_images/  →  carousel PNGs + reels + captions
```

1. **Get the script.** In Apex Studio, type today's topic (optional) and click **Copy GPT Prompt**. Paste it into **GPT (Pro)** in your browser. GPT researches the day's highest-engagement angle and returns a **`day_spec` JSON**.
2. **Paste it** into the box → **Validate** (instant schema check with clear errors).
3. **Generate** **Image**, **Video**, or **Both** → watch live progress → preview the carousel + videos in the app → **Open folder** for the files.

> Don't have GPT handy? Paste an **API key** to let the app call the model itself, or use **Plain brief** to hand-fill an editable JSON template (no LLM).

---

## Quick start

### Prerequisites
- **Windows** (the renderers and `.bat` launchers are Windows-oriented).
- **Python 3.10+** on your PATH.
- **Google Chrome** (used headless as the rendering engine — auto-detected in the usual install locations).

### Install (one time)
Double-click **`setup.bat`**. It:
1. installs the Python packages (`flask`, `kokoro-onnx`, `soundfile`, `imageio-ffmpeg`, `numpy==1.26.2`, `scipy`, `Pillow`), and
2. downloads the **Kokoro voice model** (~350 MB) into `assets/kokoro/`.

> Manual install equivalent: `pip install -r requirements.txt`, then download
> [`kokoro-v1.0.onnx`](https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx)
> and [`voices-v1.0.bin`](https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin)
> into `assets/kokoro/`.

### Run (every day)
Double-click **`run_studio.bat`** → a browser tab opens at **http://127.0.0.1:5000**.

---

## The `day_spec.json` contract

One flat, GPT-friendly JSON drives the whole post. It has an optional `carousel` block and an optional `video` block (include either or both):

```jsonc
{
  "id": "snake_case", "date": "YYYY-MM-DD", "topic": "...", "theme": "dark",
  "carousel": {
    "kicker": "Speed System",
    "slides": [ /* 5 slides: cover · problem(+meter) · reframe · build/growth fix · CTA */ ],
    "linkedin": { "caption": "...", "hashtags": ["#≤3"] },
    "fb":       { "caption": "...", "hashtags": ["#8-15"] }
  },
  "video": {
    "kicker": "Speed System", "music_mood": "driving|uplift|tense",
    "motif_name": "speedometer|countring|none", "motif_scenes": [0,2],
    "narration": [ { "text": "...", "speed": 1.0 }, /* x6 beats */ ],
    "scenes":    [ /* x6 kinetic-text beats */ ],
    "caption": "..."
  }
}
```

Conventions: wrap **one** word per headline in `**double asterisks**` → it renders **amber**; any caption/CTA containing `"AUDIT"` is auto-styled.

- **Full schema + rules + a complete worked example:** [`GPT_PROMPT.md`](GPT_PROMPT.md) (this *is* the prompt you paste into GPT).
- **A ready, valid example:** [`day_spec.example.json`](day_spec.example.json).
- **Validation + HTML assembly:** [`apex_spec.py`](apex_spec.py) — `load()`, `validate()`, and the builders the renderers call.

---

## Outputs (in `generated_images/`)

- **Carousel:** `linkedin-dark/`, `linkedin-light/`, `fb-dark/`, `fb-light/` — five `01–05.png` each (1080×1350) — plus `linkedin.md` and `fb.md` captions.
- **Video:** `video/instagram_reel.mp4` (9:16, 1080×1920) + `video/linkedin_video.mp4` (4:5, 1080×1350) + `video.md` caption.

---

## How the rendering works (offline pipeline)

- **Images** — each slide is HTML/CSS/SVG → headless Chrome `--screenshot` at 2× device scale → Pillow **LANCZOS** downscale to a crisp 1080×1350 PNG. Deterministic and reproducible.
- **Video** — a deterministic JS `render(t)` is scrubbed frame-by-frame via Chrome (`?t=<seconds>`), composited, then encoded to **H.264 / yuv420p + AAC** with **imageio-ffmpeg** (bundled binary — no system ffmpeg needed).
- **Audio** — **Kokoro** neural TTS for a natural voiceover, **procedural numpy/scipy** music (per-video mood), and synthesized SFX, mixed with ffmpeg sidechain ducking (VO > music > SFX) and normalized to **−14 LUFS**.

Per-frame Chrome scrubbing is the deliberate trade-off behind "zero extra dependencies + fully reproducible": image render ≈ **1 min**, full video render ≈ **30–45 min** (live progress shown in the UI).

---

## Drive it from Claude / any AI IDE (no GUI)

The whole system is plain Python + a JSON contract, so any tool can run it headless:

```bash
# set the spec, then run either/both renderers
set APEX_SPEC=day_spec.json   &&  python build_today_pack.py    # carousel
set APEX_SPEC=day_spec.json   &&  python build_today_video.py   # video
```

With no `APEX_SPEC`, the renderers fall back to built-in defaults. Hand an AI IDE the design specs ([`img-context.md`](img-context.md), [`video-context.md`](video-context.md)) + the contract ([`apex_spec.py`](apex_spec.py) / [`GPT_PROMPT.md`](GPT_PROMPT.md)); it produces a `day_spec.json` and runs the two scripts. The GUI just makes that one click. See [`STUDIO.md`](STUDIO.md).

---

## Project structure

| Path | What it is |
|---|---|
| `apex_studio.py` | The local web GUI (Flask) — prompt, validate, generate, live progress, preview. |
| `apex_spec.py` | The `day_spec` contract: `load()`, `validate()`, HTML/scene assembly. |
| `build_today_pack.py` | Carousel renderer (HTML → Chrome → PNG). Reads `APEX_SPEC`. |
| `build_today_video.py` | Video renderer (frame-scrub + Kokoro VO + music/SFX → MP4). Reads `APEX_SPEC`. |
| `video_concepts.py` | Animated SVG **motif registry** (`speedometer`, `countring`, `none`) + default concept. |
| `GPT_PROMPT.md` | The master prompt you paste into GPT (schema, brand, rules, research links, example). |
| `day_spec.example.json` | A complete, valid example spec. |
| `img-context.md` / `video-context.md` | Design, motion, and audio specifications. |
| `DISTRIBUTION.md` | Where else to post — a 2026 channel/repurposing plan for the brands. |
| `STUDIO.md` | The no-IDE / any-IDE operating guide. |
| `logos/` | Brand logos + color variants used at render time. |
| `setup.bat` / `run_studio.bat` / `requirements.txt` | One-time setup, daily launch, deps. |

---

## What's **not** in this repo (and why)

To keep the repo lean and within GitHub's file-size limits, three things are git-ignored and generated/restored locally:

- **`assets/`** — the Kokoro voice model (~350 MB; the `.onnx` alone exceeds GitHub's 100 MB limit). **`setup.bat` downloads it** on first run.
- **`generated_images/`** — produced output (carousels + reels). Re-created every time you generate.
- **`extra/`** — legacy/experimental scripts and earlier artifacts, organized but not part of the running app.

(Also ignored: `__pycache__/`, the transient `day_spec.json`, and scratch files. See [`.gitignore`](.gitignore).)

---

## Brand & design system (in one breath)

Monochrome editorial/Swiss layout, **ink `#171717`** + off-white, with a single **amber `#FFBE0B`** accent on exactly one load-bearing word per headline. Voice: direct, proof-led, contrarian, zero fluff — turn a service into a problem the reader feels. Audience: Pakistan (Rs, WhatsApp/DM leads) + international B2B. CTA: `DM "AUDIT"`. Slide 4 / the video's fix beat split into **BUILD** (Apex IT) and **GROWTH** (Apex Marketings) chips. Full detail in [`img-context.md`](img-context.md) and [`video-context.md`](video-context.md).

---

## Tech stack

Python · Flask · headless Google Chrome (render engine) · Pillow (LANCZOS) · Kokoro (`kokoro-onnx`, onnxruntime) TTS · numpy/scipy (procedural music + SFX) · imageio-ffmpeg (bundled H.264/AAC encoder). No build step, no cloud, no recurring cost.

---

## Troubleshooting

- **Video render fails immediately / "model not found"** → run `setup.bat` (the Kokoro model must be in `assets/kokoro/`).
- **"Chrome not found"** → install Google Chrome, or edit the `CHROME` fallback path in `build_today_pack.py`.
- **`numpy`/`scipy` import error** → ensure `numpy==1.26.2` (newer numpy breaks the pinned scipy): `pip install numpy==1.26.2`.
- **Port 5000 busy** → close the other app or change the port at the bottom of `apex_studio.py`.
- **"A job is already running"** → only one render runs at a time; wait for it to finish.

---

*Internal tooling for Apex IT Solutions & Apex Marketings. All rights reserved by the owner.*
