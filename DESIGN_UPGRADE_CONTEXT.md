# Apex Studio — Design System Context (for GPT‑5.5 Deep Research)

> **Read this entire file before answering.** It is the ground truth for a deep‑research task whose prompt lives in `DESIGN_UPGRADE_PROMPT.md`. Your proposals must fit the **exact** technical pipeline and constraints described here. Generic "good design" advice that ignores these constraints is useless — every technique you propose must be implementable in a **fully‑offline, deterministic, headless‑Chrome, 2D HTML/CSS/SVG** renderer with **no paid services and no Node toolchain**.

---

## 0. TL;DR — what you are being asked to improve

Apex Studio is a **free, offline, Python + headless‑Chrome engine** that auto‑produces a daily social media post for two sister B2B companies: a **5‑slide image carousel** *and* a **~35‑second narrated vertical video**. It already works and looks good ("professionally dark, glassmorphism, animated 2D vector fields, kinetic type"). 

The goal: make every day's output look like **a senior designer with 15+ years of experience spent hours hand‑crafting it**, and make it **dramatically, visibly different every single day** (a true generative design system), while staying **100% offline, free, brand‑correct, and deterministic**. We want concrete, prioritized, implementation‑ready upgrades to the design/motion/typography/color/layout/composition systems — not vague inspiration.

---

## 1. What Apex Studio is

- A daily "content factory" run by the owner (a solo operator) on a **Windows 11** machine with **Python 3.13** and **Google Chrome** installed.
- Each run produces, **fully offline** (no network at render time):
  - **Carousel:** 5 still slides, **1080×1350 px**, for LinkedIn and Facebook.
  - **Video:** a **~35s narrated vertical video** in two aspect ratios — **Instagram 1080×1920 (9:16)** and **LinkedIn 1080×1350 (4:5)** — with voiceover, procedural music, SFX, and on‑screen kinetic graphics.
  - **Captions:** ready‑to‑paste platform captions (`video.md`, `linkedin.md`, `fb.md`).
- The renderer is **HTML/CSS/JS rendered by headless Chrome**. For the video, Chrome is driven over the **DevTools Protocol**: the page exposes a pure JavaScript function `render(t)` (t = seconds), and Python calls `render(t)` then screenshots, frame by frame (30 fps), then ffmpeg encodes frames + audio into an MP4. (This is the same idea as Remotion, but with **no Node and no React** — just vanilla HTML/CSS/SVG/JS.)
- There is a one‑command entry (`python build_today.py`) and a small Flask GUI (`apex_studio.py`).

---

## 2. The two brands & the creative thesis

- **Apex IT Solutions** = the **BUILD** brand. Real services: Website Development, Application Development (iOS/Android/React Native/Flutter), DevOps & Cloud, 3D Modeling/Animation, technical CRO/performance. Rendered as the **neutral** axis (ink `#171717` / off‑white).
- **Apex Marketings** = the **GROWTH** brand. Real services: SEO, Google/Meta Ads, Social Media Management, Instagram Growth, E‑commerce, Lead Generation, Branding (packages from ~Rs 40k). Rendered as the **amber** accent (`#FFBE0B`).
- One **Rawalpindi, Pakistan** team serving **Pakistan + USA / UK / UAE / Saudi / Canada**.
- **Thesis (every post co‑brands both):** **"Build the system. Turn it into demand."** Apex IT builds it; Apex Marketings turns it into demand. The "fix" beat is always co‑branded (a Build column + a Growth column).
- **Signature brand mark:** a dual‑brand lockup ("APEX IT SOLUTIONS • APEX MARKETINGS") appears on every slide and every video frame, plus the **amber `#FFBE0B`** accent is the single signature color.

## 3. Audience & voice

- Founders / owners / marketing leads — **Pakistan** (currency **Rs**, **WhatsApp**/DM leads) + international B2B.
- Voice: **direct, proof‑led, contrarian, zero fluff.** Each post turns a service into a **problem the reader feels**, then reframes so the co‑branded fix is the obvious next move.
- Every post: a contrarian **hook** that inverts a belief, exactly **one** concrete verifiable number (Rs / seconds / %), and a CTA that always contains **`DM "AUDIT"`** (a free audit).

---

## 4. The deliverables — exact specs

| Artifact | Dimensions | Count | Notes |
|---|---|---|---|
| Carousel slide | 1080×1350 | 5 slides × {LinkedIn, Facebook} | Currently rendered in the **dark "lush"** look only (light theme dropped in lush mode). PNG. |
| Instagram video | 1080×1920 (9:16) | 1 | ~35s, 30fps, H.264 + AAC 48kHz |
| LinkedIn video | 1080×1350 (4:5) | 1 | same content, reframed |

- **The 5 carousel slides map to a 5‑beat story:** (1) Hook, (2) Problem (+ a "meter" data bar), (3) Reframe, (4) The Fix (Build chips + Growth chips, co‑branded), (5) CTA.
- **The video is a 6‑beat story:** Hook → Problem → Peak (the punchy data line) → Reframe → Fix → CTA. Beat durations are derived from the voiceover length (VO‑driven timeline). Total ≈ 29–36s.

---

## 5. The technical pipeline — **your proposals MUST fit this**

### 5.1 Stack & philosophy
- **Python 3.13** orchestrates; **headless Google Chrome** renders HTML/CSS/SVG/JS. **ffmpeg** (via `imageio-ffmpeg`) encodes. **No Node, no React, no Remotion, no build step.** Dependencies are tiny: `flask, kokoro-onnx, soundfile, imageio-ffmpeg, numpy, scipy, Pillow`.
- **Fully offline at render time.** A one‑time `fetch_assets.py` downloads fonts + icons (cached + hashed); after that, nothing touches the network. Fonts are embedded as base64; icons are inlined SVG.
- **Free forever.** The owner has **no budget for paid APIs**. They have ChatGPT Pro, Gemini Pro, Claude Max (web UIs — *not* usable as paid programmatic APIs) and a **Canva Student** account (no Connect/Autofill API). **Do not propose anything that costs money or requires a paid/served API, a Node toolchain, or cloud rendering.**

### 5.2 The `render(t)` determinism contract — **CRITICAL**
The video is captured by calling a pure JS function `render(t)` for each frame and screenshotting. For this to work and stay reproducible, the render path obeys strict rules. **Every animation/motion technique you propose must obey these or it cannot be used:**

- ✅ **ALLOWED:** anything that is a **pure function of `t`** — CSS `transform`/`opacity`/`filter`/`clip-path`/`background-position`/gradient stops set from JS using `t`; inline SVG with attributes computed from `t`; `getComputedStyle`‑free math; easing functions written in JS; SMIL‑free SVG; deterministic pseudo‑randomness **seeded in Python** and baked into the HTML/JS as constants.
- ❌ **FORBIDDEN inside render:** `requestAnimationFrame`, CSS `transition`/`@keyframes` animations (they depend on wall‑clock), `Math.random()`, `Date.now()`/`new Date()`, network/font/async loads, video/canvas timers, or anything whose output depends on real time or machine state. All randomness is rolled **once** in Python (from a seed) and written into the page as fixed numbers.
- **Seeding model:** a single integer **seed** (from `spec.seed` or derived from `id`+`date`) drives *all* randomness — palette choice, field choice, element positions/phases/speeds, layout, type, motion params. Same seed ⇒ same design. This is what enables "different every day, reproducible on demand."
- **Known caveat (not your problem to solve):** the glassmorphism `backdrop-filter: blur()` composites through Chrome's SwiftShader GL backend and is **not byte‑identical** across re‑renders (sub‑pixel jitter). This is harmless — each frame is rendered once per pass. Don't propose removing the glass to "fix determinism"; the HTML is deterministic, which is what matters.

### 5.3 Audio pipeline (offline, procedural)
- **Voiceover:** Kokoro TTS (`af_heart` voice), offline ONNX. 6 narration lines, with a per‑beat **speed arc** (slower on the problem/reframe beats).
- **Music:** **procedural** (numpy synthesis), 3 moods — `driving` (120bpm minor, arp), `uplift` (110bpm major, arp), `tense` (92bpm minor) — saw pads + sub sine + arpeggiator, low‑pass filtered.
- **SFX:** procedural — `whoosh`, `tick`, `thud`, `riser`, `chime`, cued to beats.
- **Mix (ffmpeg):** music bed at volume 0.16, **sidechain‑ducked** under the VO (ratio 16) and SFX, then `loudnorm` to **‑14 LUFS**. (Audio is reasonably mature; the priority is *visual* design, but suggestions for tasteful audio polish are welcome.)

---

## 6. The current design system (what already exists)

### 6.1 The "lush" look (`apex_lush.py`) — the current premium video + carousel style
- **Professionally dark background:** 6 seeded dark palettes — `obsidian, graphite, deep_navy, deep_teal, ink_violet, ember_noir` — each a near‑black base (`#06070b`) with a faint deep tonal gradient‑mesh wash + one soft amber glow (low alpha), desaturated mesh, deep vignette.
- **Animated 2D vector "field"** picked per video from the seed (or pinned via `APEX_FIELD`): `galaxy` (twinkling, slowly rotating starfield), `bubbles` (drifting glowing orbs), `particles` (flowing dots), `orbits` (concentric dashed rings + orbiting dots). Built as positioned divs/SVG with per‑element phase/speed; animated in `render(t)`.
- **Glassmorphism content card:** `backdrop-filter: blur(28px)`, translucent white gradient fill, soft border + big shadow. Holds the beat's text.
- **Per‑beat "concept vectors":** a row of 3 glowing icon tiles inside the card, plus 3–4 large faint floating topic icons in the open area — all **auto‑derived from the headline text** (keyword → Lucide icon).
- **Type:** bold 900 weight headline, one word per headline rendered as an **amber gradient "punch"** word that scales in on the beat; tag/kicker pill; sub line; chips; CTA.
- **Footer every frame:** amber progress bar (video) or 5 slide‑position dots (carousel), and the dual‑brand lockup.

### 6.2 The art‑direction / lookbook system (`apex_art.py`) — the *classic* look (still used for non‑lush)
Before the lush pivot, there was (and still is) a richer **seeded art‑director** with **12 "lookbooks"** (e.g. `blueprint`, `kinetic_bold`, `magazine`, `noir_editorial`, …). Each lookbook bundles: a **world** (background layer set: grain, dot‑grid, glow, mesh, rings, spotlight, beams, scan lines, grid), **accents** (corner brackets, guides, ghost numerals, ticks, HUD, radar), **tones** (amber_signature, duotones, monos, editorial cream), **fonts** (display + body + weight + case + tracking), **d3** (CSS‑3D modes: depth parallax, card stack, prism, extruded type), **layout** (centered, left‑editorial, split, asymmetric‑hero, grid, full‑bleed type), and seeded motion/jitter ranges. It also has per‑scene placement and concept "set‑pieces" (`apex_worlds.py`: feed_cards, gauges, funnel_drips, coin_field, stair_climb, node_net, scan_grid). **This system is rich but the owner felt the *output* still looked too uniform/"basic"** — which is what triggered the lush pivot. **A big opportunity is to fuse the lush look with this lookbook variety so each day picks a genuinely different — yet equally premium — art direction.**

### 6.3 Randomization & anti‑repeat model (today)
- A seed selects: lush palette (1 of 6), field (1 of 4), and (in classic mode) a lookbook (1 of 12) + layout + type + d3 + motion params.
- `apex_concept.py` picks 1 of **12 content pillars** with **anti‑repeat memory** (`art_memory.json` keeps the last few used pillars so topics rotate). The look has its own anti‑repeat memory.
- **Reality check:** the *visible* daily variety is currently modest — mostly palette + field + which headline. The lookbook/layout/type/motion axes are under‑exploited in the lush path. **The opportunity is a true generative design system: many independent, seeded design axes that combine into a fresh, senior‑grade composition every day.**

### 6.4 The `day_spec` schema (the JSON that drives a post)
A post is described by one JSON object (`day_spec.json`) with two sections:
- `carousel`: `kicker`, `slides[5]` (each: `headline[]`, `sub`, optional `tag`, `motif`, `meter{head,left,right}`, `build_chips[]`, `growth_chips[]`, `cta`, `icons[]`), plus `linkedin{caption,hashtags[≤3]}` and `fb{caption,hashtags[8‑15]}`.
- `video`: `kicker`, `music_mood`, `motif_name`, `narration[6]` (text + speed), `scenes[6]` (headline[], tag, sub, build/growth chips, cta, `punch_at`, `big`), `caption`.
- Optional art‑direction fields are **lenient** (unknown/invalid values fall back). There is a `seed` and a `look` ("auto" or a lookbook name).
- The spec can be **authored by GPT** (paste path) *or* generated **locally & offline** by `apex_concept.py` (the 12‑pillar generator). Either way it is validated by `apex_spec.validate()`.

### 6.5 Assets available offline
- **Fonts (10 families, Google Fonts, OFL):** Archivo, Inter, Sora, Space Grotesk, **Fraunces** (serif display), **Newsreader** (serif text), Syne, Manrope, **Bricolage Grotesque**, Geist — multiple weights each. (You may recommend *adding* more OFL fonts via `fetch_assets.py`, but they must be free/OFL and fetched once.)
- **Icons:** ~49 **Lucide** SVG icons (ISC license), inlined and theme‑tinted; auto‑selected from text keywords.
- **Texture:** a base64 SVG film‑grain; CSS gradient meshes; glass blur.

---

## 7. Motion / animation vocabulary today (video)
All driven by `render(t)`, deterministic:
- Field animation (bubbles rise/wrap, stars twinkle, particles flow, orbs orbit, galaxy container slow‑rotates).
- Background mesh slow drift.
- Scene **enter/exit** transitions: fade + translateY + slight scale (one family, `outCubic`/`inQuad`).
- Per‑beat concept‑icon **pop** (staggered scale + small rotate).
- Headline **punch** word scales 0.7→1.0 at `punch_at`.
- Progress bar fill.
- (Classic path also has more transition types and kinetic‑text modes, plus CSS‑3D — under‑used in lush.)
**Gap:** the motion is tasteful but limited to ~one transition family and a few effects; a senior motion designer would layer staggered reveals, masking/clip‑path wipes, line‑draw SVG, number tickers, parallax depth, beat‑synced accents, and varied per‑day motion "personalities."

---

## 8. Design history — what we tried & learned (so you don't repeat dead ends)
1. **HUD/editorial (classic lookbooks):** rich system, but owner repeatedly called the output "basic / too uniform."
2. **CSS‑3D + WebGL/three.js 3D:** real 3D was attempted; WebGL works in headless Chrome only via slow software SwiftShader (~heavy), and 3D was often invisible/finnicky. **Abandoned WebGL** as a dependency.
3. **Lush 2D vectors (current):** pivoted to pure 2D CSS/SVG vector fields + glassmorphism + gradient type — fast, deterministic, premium. Then **"professionally dark"** per owner request.
4. **Lesson:** the winning path is **2D HTML/CSS/SVG, deterministic, offline** — but pushed to a *much* higher craft ceiling and *much* more daily variety. Don't propose WebGL/Node/paid tools.

---

## 9. Constraints & non‑negotiables (hard rules for every proposal)
1. **Offline & free.** No paid APIs, no served LLM calls at render time, no cloud render, no Node/npm, no Canva API. One‑time free asset downloads (OFL fonts / permissive SVG/Lottie‑JSON) are OK.
2. **Deterministic `render(t)`.** No rAF / CSS transitions / `Math.random` / `Date.now` inside render. All randomness seeded once in Python.
3. **2D only.** HTML/CSS/SVG/JS in headless Chrome. No WebGL dependency. (Clever 2.5D via CSS transforms/`perspective` is fine if deterministic and reliable in headless.)
4. **Brand rules kept:** dual‑brand lockup on every frame/slide; amber `#FFBE0B` as the signature accent (a professionally‑dark base is the current direction); the co‑branded Build/Growth "fix"; CTA always contains `DM "AUDIT"`; one concrete number per post; contrarian hook.
5. **Performance budget:** video is ~1000+ frames at ~1.7 fps on this machine (software render). Keep per‑frame cost sane — avoid huge per‑frame blur on full‑screen layers, thousands of DOM nodes, or anything that tanks frame time. Carousel is only 5 stills (can be heavier).
6. **Legibility & safe zones:** text must stay readable (sound‑off social), inside platform safe areas, high contrast on dark.
7. **No auto‑posting / no scraping.** Out of scope.

---

## 10. Known gaps & opportunities (where the biggest wins are)
- **Daily variety is too shallow.** Need a true **generative design system**: many independent seeded axes (palette, type pairing, grid/layout, composition archetype, motion personality, transition family, field, texture/material, accent treatment, color‑grade) that combine to a fresh, on‑brand, senior‑grade look each day — with anti‑repeat across all axes.
- **Typography is under‑designed.** 10 great fonts exist but pairing/scale/rhythm/optical‑size/tracking systems are basic. Editorial typographic craft (display+text pairings, hierarchy, kerning, ligatures, mixed weights, kinetic type) is a huge lever.
- **Layout/composition is mostly one centered/bottom card.** Senior work uses varied grids, asymmetry, rule‑of‑thirds, tension, negative space, full‑bleed type, editorial columns.
- **Motion is one transition family.** Need a richer, deterministic motion/transition library and per‑day motion "personalities" (e.g., precise/Swiss vs energetic/kinetic vs calm/editorial).
- **Color is good but could be a real system** (palette theory for premium dark, accent harmonies, gradient grading, duotones) seeded per day.
- **Data‑viz vocabulary is thin** (one "meter" bar). Deterministic mini‑charts (animated bars/lines/donuts/number tickers drawn from the post's one number) would add credibility + motion.
- **Texture/material/depth** (grain, glass, glow, noise, soft shadows, light leaks, paper/ink) could be a seeded material system for richness.
- **Carousel↔video coherence:** they now share palette+field; push further so a day's whole set looks art‑directed as one campaign.

---

## 11. File map (where to implement)
| File | Role |
|---|---|
| `apex_lush.py` | The lush look. `build_lush_html(aspect, concept, tl)` (video, full `render(t)` page) + `build_lush_slide_html(slide, idx, total, kicker, seed, W, H)` (static carousel slide). **PALETTES**, `_field()`, `_cvec_row()`, `_scene_inner()`, `_slide_inner()`. **Most design changes land here.** |
| `apex_art.py` | Seeded art‑direction: 12 lookbooks, palettes, fonts (`fontface_css`), layouts (`layout_css`), type (`type_css`), CSS‑3D (`d3_css/d3_html`), world/accents, `choose_look`, `remember_look`, `derive_seed`. The variety engine to fuse with lush. |
| `apex_spec.py` | `day_spec` schema, `validate()`, HTML builders for carousel/video scenes, text helpers (`bold_punch`, `bold_static`, `_auto_icon_names`, chip/icon helpers). |
| `apex_concept.py` | Offline generator: **12 pillars** + phrasing banks + anti‑repeat; builds a full valid `day_spec`. |
| `apex_icons.py` | Lucide icon loader + keyword→icon mapping. |
| `apex_worlds.py` | Concept‑custom background set‑pieces (feed_cards, gauges, funnel_drips, coin_field, stair_climb, node_net, scan_grid). |
| `build_today_video.py` | VO (Kokoro) + procedural music/SFX + ffmpeg mix; timeline (`build_timeline`); `write_captions()`. |
| `fast_render.py` | DevTools‑Protocol frame renderer (`render(t)`→screenshot→encode). Env: `APEX_LUSH`, `APEX_SCALE`, `APEX_FIELD`. |
| `build_today_pack.py` | Carousel renderer (classic + lush paths). |
| `build_today.py` | One‑command: carousel + video from one `day_spec`. |
| `fetch_assets.py` | One‑time font/icon fetch (+`--verify`). Add new OFL fonts / permissive SVG here. |
| `tests/smoke.py` | Offline smoke tests (validator, generator, HTML determinism). New deterministic features should be testable here. |

## 12. Environment knobs
`APEX_SPEC` (path to day_spec), `APEX_AUTO=1` (generate locally), `APEX_SEED` (pin the seed), `APEX_LUSH=1` (dark lush look), `APEX_FIELD=galaxy|bubbles|particles|orbits` (pin field), `APEX_SCALE` (device scale).

---

### One‑line summary for the model
> Propose a **prioritized, implementation‑ready upgrade** to turn a working **offline, deterministic, 2D HTML/CSS/SVG + headless‑Chrome** social‑post engine into one whose **every daily output looks like senior‑designer, hours‑of‑craft work** and is **visibly, generatively different each day** — using only **free, offline, deterministic** techniques, respecting the brand rules, and citing the exact files/functions to change.
