# Apex Daily VIDEO Post — Generation Context & Full Spec

> **Purpose.** Hand this file **plus the whole `C:\xampp\htdocs\apexsocialmedia` folder** to any AI/tool and say *"create a video for today."* This is the companion to `img-context.md` (the image/carousel spec) — read that too; the video deliberately reuses the same brand + design system. Follow this literally. Change **words/timeline only**; keep the **design system, colors, motion language, audio palette, formats, and file structure** as specified.

---

## 0. QUICKSTART — "create a video for today"

The video is produced by **`build_today_video.py`** (repo root) + the day's concept in **`video_concepts.py`**. It renders a **~37‑second, concept‑customized animated vector reel** — **Kokoro voiceover** + **per‑video procedural music** + SFX + an **animated hero vector motif** — in **two native aspect ratios** (Instagram 9:16 + LinkedIn 4:5), **dark theme**, into `generated_images/video/` (+ caption `generated_images/video.md`).

1. **One‑time setup (offline/free):** `pip install imageio-ffmpeg kokoro-onnx soundfile`, then **pin** `pip install "numpy==1.26.2"` (kokoro pulls numpy 2.x which breaks scipy). The Kokoro model auto‑caches to `assets/kokoro/` (first run downloads `kokoro-v1.0.onnx` + `voices-v1.0.bin`, ~350 MB). Verify: `python -c "import imageio_ffmpeg,kokoro_onnx,scipy,numpy,PIL"`.
2. **Pick/refresh today's concept** — edit/add an entry in `video_concepts.py` (`CONCEPTS` + `TODAY`): `kicker`, 6 `scenes` (kinetic HTML), `narration` (text + pace), `hero motif` (animated SVG + JS), `music_mood`, `caption`. Changing the concept changes the whole video (visual + voice + music). See §9.
3. **(Optional) smoke‑test:** `python build_today_video.py smoke` → synths VO+music, builds the timeline, writes `_audio_preview.wav` + one still per beat to ROOT. Eyeball, then delete.
4. **Render:** `python build_today_video.py` → synth VO + music, capture frames (~1,100 per aspect via Chrome), encode + mux. **~30–45 min** (per‑frame Chrome). Run in background.
5. **Verify** (§11): both MP4s play; 1080×1920 & 1080×1350, 30 fps, H.264 yuv420p + AAC 48 kHz, ~37s; audio ≈ −14 LUFS (VO above music + SFX); folder intact.

Do **not** change the palette, fonts, motion model, audio palette, dimensions, or output structure unless the human asks. Those are the system.

---

## 1. What this is

A daily **motion‑graphics video** companion to the 5‑image carousel: premium **kinetic typography + vector motion** (no stock footage, no AI‑video, no talking head) on the Apex dark theme, with **synthesized sound effects** synced to the motion. It's the *moving version of today's carousel post* — same brand, same "rent vs own / build → demand" thesis, same `DM "AUDIT"` CTA. Optimized for Instagram Reels + LinkedIn feed, autoplay‑muted‑friendly (the on‑screen kinetic text doubles as captions), and built to loop.

---

## 2. Relationship to the image pipeline (reuse, don't duplicate)

`build_today_video.py` does `import build_today_pack as pack` and **reuses verbatim**: `pack.PALETTES` (dark+light color tokens), `pack.token_map()`/`pack.LOGO_TOKENS`/`pack.inject()` (base64 logo system from `logos/variants/`), `pack.GRAIN` (film‑grain data‑URI), `pack.hex_rgb()`, `pack.bgop()`/`pack.BG_INTENSITY`, `pack.rings_svg()` + `pack.guides()` (background vector layers), the **Segoe UI** font stack, and the **light‑bg flatten fix** (composite the transparent Chrome screenshot onto a solid `base`‑color RGBA before `convert("RGB")`). Brand facts, voice, audience, hashtags, and the daily content all come from `img-context.md` — read it for those. This file only covers what's *new* for video: motion, audio, and MP4 assembly.

---

## 3. The deliverable — exact output

Two MP4s in **`generated_images\video\`** + the **caption at top level** (`generated_images\video.md`, sibling to `linkedin.md`/`fb.md`):

```
generated_images/
├─ video/
│   ├─ instagram_reel.mp4   (1080×1920, 9:16, ~34s)
│   └─ linkedin_video.mp4   (1080×1350, 4:5,  ~34s)
└─ video.md                 (daily video caption — copy‑paste, for IG + LinkedIn)
```

- **Specs:** 30 fps, **H.264** (`yuv420p`) + **AAC** 192k @ 48 kHz, `+faststart`, loudness ≈ **−14 LUFS**. CRF 18 / preset slow. ~34s (VO‑driven). Files ~15–60 MB.
- **Audio (v3):** **Kokoro** neural voiceover (offline, natural) + a **per‑video procedural music** bed + SFX, all **ducked under the voice** (−14 LUFS). Caption (`video.md`) mirrors the narration.
- **Daily concept system (v3):** content + art direction (scenes, narration, hero **vector motif**, music mood, caption) live per‑topic in `video_concepts.py` (`get_today()`); the brand/design is locked in `build_today_video.py`. Today ships the **site‑speed** concept with an animated **speedometer** motif. Change the concept → the whole video (animation/voice/music) changes.
- **Aspects are rendered NATIVELY** (aspect‑aware layout), never cropped: Instagram 9:16 full‑screen (respects IG safe zones — key text kept clear of top ~120 / bottom ~330 px); LinkedIn 4:5 feed‑dominant.
- **Theme:** dark only (video reads most premium dark).
- **Coexistence:** the `video/` folder + `video.md` live in `generated_images/` alongside the carousel's 4 folders + 2 `.md`. `build_today_pack.cleanup_output()` whitelists `"video"` (in `KEEP_DIRS`) and `"video.md"` (in `KEEP_FILES`), so the image pipeline will NOT delete them. The video script only ever clears its own `video/` dir + rewrites `video.md`.

---

## 4. Format / platform specs (2026)

| | Instagram (Reel) | LinkedIn (feed) |
|---|---|---|
| Aspect / px | 9:16 — **1080×1920** | 4:5 — **1080×1350** |
| Length | 15–30s ideal | 30–60s ok; ~21s fine |
| fps / codec | 30 / H.264 + AAC | 30 / H.264 + AAC |
| Safe zone | top ~120, bottom ~330 px (UI) | minimal |
| Captions | required (muted autoplay) — on‑screen kinetic text serves this | required — same |
| Loudness | ~−14 LUFS | ~−14 LUFS |
| Hook | first ~2s decisive | first ~2s decisive |
| Loop | seamless‑ish ending rewarded | same |

One render per aspect (same animation + audio, native layout). Defined in `ASPECTS` in `build_today_video.py`.

---

## 5. Motion / design system (fixed)

Same monochrome **+ single amber `#FFBE0B`** look as the images (Apex IT = ink/off‑white neutral; Apex Marketings = amber). Persistent frame across the whole video: **top** = kicker (`OWNED DEMAND SYSTEM`) + neutral|amber split‑bar; **bottom** = the co‑brand logo lockup (`▸ APEX IT SOLUTIONS × APEX MARKETINGS ◣`) + a thin **progress bar** that fills 0→100%. The **middle stage** cross‑fades through 5 scenes. Background (grain, dots, glow, rings, mesh, vignette, corner brackets) is reused and kept alive with **very slow drift** (glow breathes ±1.5%, rings rotate ~1.2°/s, mesh ±8px) — premium, never busy.

**Deterministic render engine** (`build_anim_html(aspect)`): a single self‑contained HTML whose JS `render(t)` reads `?t=<seconds>` (`URLSearchParams`) and sets every transform/opacity/width from `t` only — **no** real‑time animation/`requestAnimationFrame`/CSS transitions. Each frame is therefore reproducible (open `anim.html?t=5.6` in a browser to inspect any moment). The timeline `{total, fps, scenes:[{id,start,end}]}` is injected as JSON. Easing lib (pure JS math): `outQuad, inQuad, outCubic, inOutCubic, outBack` (overshoot for scale‑punch).

**Motion techniques used** (premium): staggered reveals (`.stag`, 0.10s gaps), scale‑punch on the load‑bearing amber word (`.punch` with `data-at`, `outBack`), the meter bar filling 0→84% with a knob, scene cross‑fades with rise‑in/rise‑out, intro draw‑on of the frame. **Avoid** (reads cheap): linear tweens, excessive cuts, spins/bounces, glitch, low‑contrast text, audio out of sync. Amber only on the 1 key word per scene (rent / cracked / own / asset / growth).

---

## 6. Audio (v3) — Kokoro voiceover + per‑video music + ducked SFX

**Voiceover (offline, free):** **Kokoro** neural TTS via `kokoro-onnx` (`VOICE=af_heart`, model cached in `assets/kokoro/`). `synth_line(text, speed)` renders each narration line (per‑line `speed` conveys emotion/pace); clips resample 24k→48k and sit at each scene's lead‑in (frame‑locked). Polished via ffmpeg `-af` (highpass 85, lowpass 13.5k, `acompressor`, +2 air @8k, whisper `aecho`). Natural, human, real‑time on CPU. (Piper is retired; Chatterbox = optional future "more emotion" but heavier.)

**Per‑video music:** `make_music(mood, seconds)` — a **procedural** numpy/scipy engine (pads + sub‑bass + arpeggio over a mood‑mapped chord progression: `driving`/`uplift`/`tense`), deterministic, no deps. The mood comes from the day's concept. (Stable Audio Open is the optional AI upgrade; skipped here for reliability.)

**SFX bed:** numpy/scipy (whoosh/tick/thud/riser/chime), cue times derived from the scene timeline (frame‑locked).

**Mix (3‑way duck):** `build_audio()` ffmpeg `-filter_complex` — music `volume=0.5` then **`sidechaincompress`‑ducked under the VO**, SFX lightly ducked under the VO, `amix` the three, then `loudnorm I=-14:TP=-1.5:LRA=11`. Result: **VO on top → music bed under → SFX accents**, integrated ≈ −14 LUFS.

---

## 7. Storyboard / narration (~34s, 30fps, dark, VO‑driven, loop‑friendly)

**VO‑driven:** each beat lasts as long as its narration clip (+lead‑in 0.38s / tail 0.55s), so `TOTAL` is computed (~34s), not fixed. 6 beats; `NARRATION` (voiceover) + `scenes_html()` (on‑screen kinetic text); amber on the **bold** word.

| beat | voiceover (Piper) | on‑screen | motion + SFX |
|---|---|---|---|
| s1 | "…the truth about paid ads — they're rent." | "Ads are **rent**." | hook rise + **rent** punch; light sweep · whoosh+thud |
| s2 | "…you stop paying, the traffic drops to zero." | "Stop paying. Traffic hits **0**" | count‑down to 0 · riser+thud |
| s3 | "…most teams scale that rent on a cracked foundation…" | "Scaling rent on a **cracked** foundation." + meter | meter 0→84% · riser+chime |
| s4 | "…a fast site plus SEO? You own it — it compounds." | "A site + SEO, you **own** it." | reframe + **own** punch · thud |
| s5 | "…fix the asset first. Apex IT builds… Apex Marketings…" | "Fix the **asset** first." + Build/Growth | divider draw + chips stagger · ticks |
| s6 | "Stop renting your growth. DM AUDIT…" | "Stop renting your **growth**." + DM "AUDIT" | **growth** punch; CTA + lockup · chime |

Throughout: persistent frame (kicker+split‑bar top, lockup+progress bar bottom), **mask‑wipe** scene transitions, subtle **parallax + camera push**, drifting amber **particles**, anticipation/overshoot easing. On‑screen text doubles as muted‑view captions; the VO expands it.

---

## 8. Pipeline — how `build_today_video.py` works

**Environment (verified):** Windows; Python 3.12 + numpy 1.26 + scipy 1.15 + Pillow 10.1 + imageio 2.37 present; **`imageio-ffmpeg`** (the one required install) gives the ffmpeg binary via `imageio_ffmpeg.get_ffmpeg_exe()`; Chrome 149 at `C:\Program Files\Google\Chrome\Application\chrome.exe`. No playwright/cairosvg/pydub/Node needed.

Flow:
1. `mix_audio()` → one shared `sfx.wav` (temp) from `cues()`.
2. For each aspect: write `anim_<aspect>.html` (temp), then **`capture_frames()`** loops frames — per frame, launch headless Chrome `--screenshot --force-device-scale-factor=2 --window-size=W,H "file:///anim.html?t=<t>"`, composite onto theme base (flatten fix), save `frame_%05d.png` to a temp dir. (~630 frames/aspect.)
3. **`encode()`** via the ffmpeg binary (subprocess): PNG seq → H.264 (`-pix_fmt yuv420p -crf 18 -preset slow`), mux WAV → `-c:a aac -b:a 192k -ar 48000`, `-af loudnorm=I=-14:TP=-1.5:LRA=11`, `+faststart -shortest` → `generated_images/video/<out>.mp4`.
4. Write the caption to `generated_images/video.md`; print a summary.

Frames render to `tempfile.gettempdir()/apex_vid/…` (never into `generated_images/`) and are deleted after each aspect encodes.

**Performance:** per‑frame Chrome ≈ fps×sec×aspects ≈ 30×21×2 ≈ 1,260 launches ⇒ ~15–30 min. This is the cost of zero‑browser‑dependency determinism — acceptable for a daily batch. Run in the background. (Optional speed‑up if ever desired: a persistent Playwright/CDP browser instead of relaunching Chrome — not required, not default.)

---

## 9. HOW TO MAKE A NEW VIDEO FOR TODAY (do this)

**Keep the engine, motion model, audio palette, formats, and output structure identical. Change the day's CONCEPT in `video_concepts.py`** (the brand/render is locked in `build_today_video.py`):

1. **Add a `CONCEPTS["…"]` entry** (or edit one) and point `TODAY` at it. Fields: `kicker`; `music_mood` (`driving`/`uplift`/`tense`); `caption`; `narration` = 6 `(text, speed)` lines (speed conveys emotion/pace, ~0.95–1.05); `scenes` = 6 HTML beats; `motif_svg(P)` + `motif_js` + `motif_scenes` (the animated hero vector); .
2. **6‑beat arc** (each `scene`): **s1 hook** (one **amber** punch word via `<b class="punch" data-at="0.45">word</b>`), **s2 problem**, **s3 reframe / data** (often where the hero motif peaks), **s4 reframe**, **s5 system** (Build = 2 Apex‑IT chips, Growth = 2 Apex‑Marketings chips), **s6 CTA** (ends `DM "AUDIT" …`). Use `.stag` for staggered children. Timeline is VO‑driven (each beat lasts its narration + lead‑in/tail), so `cues()` auto‑follows.
3. **Hero vector motif** — `motif_svg(P)` returns inline SVG (ids the JS animates); `motif_js` defines `window.motifSet(i, p)` (scene index + 0‑1 progress) to animate it (draw‑on, sweep, count, morph) and toggle its opacity; `motif_scenes` lists which beats show it. New motifs live next to `motif_speedometer` — add per topic (house+key, hourglass, magnet+graph, funnel, lightbulb…). This is how each day *looks* different.
4. **Voice/music/caption** vary automatically from the concept (`VOICE` swappable in `build_today_video.py`). Update the `caption` field → it's written to `generated_images/video.md`.
5. **Run** `python build_today_video.py` and verify (§11). Optionally `smoke` first.

Today's content normally matches the carousel — generate/choose the day's angle the same way `img-context.md` §10 describes, then express it as these 5 scenes.

---

## 10. Hard rules / do‑NOT

- Dark theme; **one accent only** (amber `#FFBE0B`); amber on just the 1 key word per scene.
- Minimal on‑screen text; kinetic type must stay legible at mobile thumbnail.
- **No** stock video, AI‑generated video, talking heads, robot/AI clichés, glitch, scanlines, spins/bounces, linear tweens, or audio that lags the visual.
- **SFX‑only** (no licensed music); keep ≈ −14 LUFS.
- Render natively per aspect (no cropping). Respect IG safe zones.
- Outputs go ONLY in `generated_images/video/`; never write scratch/frames into `generated_images/` (use temp). Keep the carousel's 4 folders + 2 `.md` intact.
- Both logos in the lockup; don't restyle the marks.

---

## 11. Verification & gotchas

After `python build_today_video.py`:
1. **Both MP4s exist** in `generated_images/video/`, > 200 KB, and play.
2. **Probe** (imageio‑ffmpeg has **no ffprobe** — parse `ffmpeg -i out.mp4` stderr): assert `Video: h264`, exact dims (`1080x1920` / `1080x1350`), `30 fps`, `yuv420p`; `Audio: aac`, `48000 Hz`. (The script prints this summary.)
3. **Audio present & loud enough** — a `loudnorm …print_format=json -f null -` analysis pass should report integrated ≈ −14 ±1.5 LUFS.
4. **Hook readable** — eyeball an early frame (~t=1–2s) and a frame per scene (smoke mode renders these quickly).
5. **Loop** — compare first vs last frame; ending holds the CTA/lockup, persistent frame minimizes the seam.
6. **File size** well under platform caps (expect ~10–40 MB).
7. **Folder integrity** — `generated_images/` still has the 4 carousel folders + `linkedin.md` + `fb.md` **plus** `video/`. A concurrent Gemini/Antigravity agent sometimes writes here — re‑check after running.
8. **Gotchas:** ffmpeg missing → `pip install imageio-ffmpeg`. Render seems stuck → it only logs every 30 frames; check the temp `frames_<aspect>/` count. Light‑theme black edges (if ever rendering light) → the composite‑onto‑base step. Per‑frame render is just slow, not broken.

---

## 12. Files

- `build_today_video.py` — the v3 engine: Kokoro VO (`synth_line`), procedural music (`make_music`), SFX, `build_audio` (3‑way ducked mix), `render(t)` + motif hook, capture, encode. Modes: `smoke` / default.
- `video_concepts.py` — the **daily concept registry** (`CONCEPTS`, `TODAY`, `get_today()`) + the **animated vector‑motif library** (e.g. `motif_speedometer` + its `motif_js`). This is where each day's video is defined.
- `build_today_pack.py` — imported & reused (design system, logos, textures, flatten fix); `KEEP_DIRS` includes `"video"` and `KEEP_FILES` includes `"video.md"` so the carousel cleanup preserves both.
- `assets/kokoro/` — cached Kokoro voice model (`kokoro-v1.0.onnx` + `voices-v1.0.bin`).
- `img-context.md` — the image/carousel spec + all brand/voice/content rules (read first).
- `generated_images/video/` (MP4s) + `generated_images/video.md` (caption) — outputs.
- `logos/variants/` — logo PNG tokens (dark video uses `ARROW_OFFWHITE` + `M_AMBER_BRAND`).
- **Deps (offline/free):** `imageio-ffmpeg`, `kokoro-onnx` + `soundfile`, `numpy==1.26.2`, `scipy`, `Pillow`, Chrome. (No API keys; music + SFX are pure numpy.)

*To produce today's video: edit `scenes_html()`/`cues()`/caption in `build_today_video.py`, run it, verify. Keep the design + motion + audio systems identical.*
