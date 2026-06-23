# Apex Studio — run the daily post system without an IDE

Apex Studio is a tiny local app that turns one JSON ("day_spec") into the day's **image carousel** and **narrated video**, rendering **offline and free** on your PC.

## The workflow
1. **Get the script.** In Apex Studio, type today's topic (optional) and click **Copy GPT Prompt**. Paste it into **GPT (Pro)** in your browser. GPT researches the angle and returns a **day_spec JSON**.
2. **Paste it.** Paste that JSON into the box → **Validate**.
3. **Generate.** Click **Generate Image**, **Generate Video**, or **Both**. Watch live progress, then preview the images + videos right in the app. **Open folder** to grab the files from `generated_images/`.

(Optional inputs: paste an **API key** to let the app call the model itself; or use **Plain brief** to get an editable JSON template with no LLM.)

## Run it
- **One‑time:** double‑click **`setup.bat`** (installs free tools; first video render downloads the ~350 MB voice model once).
- **Every day:** double‑click **`run_studio.bat`** → a browser tab opens at `http://127.0.0.1:5000`.

Only your own GPT step uses the internet. All rendering (images, voice, music, video) is **offline + free** (Chrome + bundled ffmpeg + local Kokoro voice + numpy music/SFX).

## Outputs (in `generated_images/`)
- Carousel: `linkedin-dark/ linkedin-light/ fb-dark/ fb-light/` (5 PNGs each) + `linkedin.md`, `fb.md`.
- Video: `video/instagram_reel.mp4` (9:16) + `video/linkedin_video.mp4` (4:5) + `video.md`.

## Drive it from Claude / any AI IDE (no GUI)
The whole system is plain Python + a JSON contract:
- **Contract:** `apex_spec.py` (schema + `validate()` + HTML assembly) and `GPT_PROMPT.md` (the full schema + rules + example).
- **Generators:** set env `APEX_SPEC=<path to day_spec.json>` then run `python build_today_pack.py` (carousel) and/or `python build_today_video.py` (video). With no `APEX_SPEC`, they use built‑in defaults.
- Brand/design/motion specs: `img-context.md` (images) and `video-context.md` (video).
So any AI IDE can: read those specs → produce a `day_spec.json` → run the two scripts. The GUI just makes that one‑click.

## Files
- `apex_studio.py` — the GUI (Flask). `apex_spec.py` — the JSON contract + assembly.
- `GPT_PROMPT.md` — the master prompt for GPT. `day_spec.example.json` — a complete example.
- `build_today_pack.py` / `build_today_video.py` / `video_concepts.py` — the renderers (read `APEX_SPEC`).
- `img-context.md` / `video-context.md` — the design/motion/audio specs. `DISTRIBUTION.md` — where else to post (channel plan).
- `setup.bat`, `run_studio.bat`, `requirements.txt`. Legacy/experimental files live in `extra/`.
