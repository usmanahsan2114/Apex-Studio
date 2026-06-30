# Apex Studio — Deep‑Research Design‑Upgrade Prompt (paste into GPT‑5.5 with deep search/research ON)

> **Attach / paste `DESIGN_UPGRADE_CONTEXT.md` together with this prompt.** That file is the ground truth for the system, constraints, and current design. Everything you propose must obey it.

---

## Your role

You are a **world‑class creative director + motion designer + brand systems designer** (15+ years, award‑winning editorial, B2B, and social‑video work) **who also deeply understands deterministic, code‑driven rendering** — generative/seeded design systems, CSS/SVG animation, kinetic typography, and frame‑scrub video pipelines (Remotion‑style, but here it's vanilla HTML/CSS/SVG/JS in headless Chrome). You think in **systems**, not one‑off mockups: reusable palettes, type scales, grids, motion grammars, and the seeded rules that combine them into something fresh every day yet unmistakably one brand.

## Your mission

Design a **prioritized, concrete, implementation‑ready upgrade plan** that makes Apex Studio's **daily** carousel + video output look like **a senior designer spent hours hand‑crafting each one**, and makes each day **visibly, generatively different** — while staying **100% offline, free, deterministic, 2D (HTML/CSS/SVG), and brand‑correct** (see constraints in the context file). The output of your research will be handed to an **AI coding agent (Claude Code) to implement directly**, so it must be precise, technical, and reference the actual files/functions named in the context.

This is **not** a request for inspiration or vague principles. It is a request for a **buildable design system + a backlog of specific techniques**, each with the exact deterministic CSS/SVG/JS pattern and the file/function to change.

---

## Step 1 — Do deep research first (use your web/deep‑search)

Research and synthesize the current best practice (2024–2026) across these areas, **then translate each finding into something implementable in this offline, deterministic, 2D pipeline.** For every external technique, explicitly note how to reproduce it with seeded CSS/SVG/JS (no WebGL, no Node, no paid tools):

1. **Award‑winning generative / seeded brand systems** (e.g. design systems where a seed drives palette, type, grid, motion — what axes they vary and how they stay coherent). How do the best "templated but never repetitive" systems achieve infinite‑feeling variety without looking random?
2. **Editorial & motion typography**: display+text pairing theory, type scales & vertical rhythm, optical sizing, tracking/kerning, mixed‑weight hierarchy, kinetic type (mask reveals, line‑by‑line, per‑word, weight/width animation, variable fonts). Which of the 10 available OFL fonts pair well, and what *additional* free OFL fonts would meaningfully expand the range?
3. **Premium dark UI / "professionally dark" color systems**: dark palette construction, accent harmonies around a fixed amber `#FFBE0B`, gradient grading, duotones, glass/glow, contrast & legibility for sound‑off social. Give concrete seeded palette recipes.
4. **Layout & composition systems for vertical social**: grid systems, rule‑of‑thirds/tension, asymmetry, negative space, full‑bleed type, editorial columns, focal hierarchy — a *library of composition archetypes* the engine can pick from per day while keeping the brand lockup + safe zones.
5. **Motion design grammar for short social video**: hook retention in the first 1–2s, staggered reveals, masking/`clip-path` wipes, SVG line‑draw, number tickers/counters, parallax depth, beat/transition families, easing libraries, micro‑interactions, and **per‑day "motion personalities"** (e.g. Swiss‑precise vs energetic‑kinetic vs calm‑editorial) — all expressible as pure functions of `t`.
6. **Deterministic data‑viz / infographics**: animated bars, lines, donuts, gauges, progress, number tickers, comparison meters — drawn in SVG/CSS from the single concrete number each post carries, as motion that adds credibility.
7. **Texture / material / depth**: grain, noise, glass, glow, soft shadows, light leaks, paper/ink, gradient meshes — a seeded "material" layer for richness without clutter.
8. **2026 B2B social best practices**: format/length/safe‑area conventions for IG Reels / LinkedIn video & carousels, caption/hook patterns, and what currently signals "premium agency" vs "template/AI‑generated."

Cite sources for non‑obvious claims.

---

## Step 2 — Respect the hard constraints (from `DESIGN_UPGRADE_CONTEXT.md`)

- **Offline & free** — no paid APIs, no Node, no WebGL dependency, no Canva API, no cloud render. One‑time free OFL font / permissive SVG/Lottie‑JSON downloads via `fetch_assets.py` are allowed.
- **Deterministic `render(t)`** — pure function of `t`; **no** `requestAnimationFrame`, CSS `transition`/`@keyframes`, `Math.random`, or `Date.now` inside render. All randomness seeded **once** in Python and baked in as constants.
- **2D HTML/CSS/SVG/JS** in headless Chrome only. Deterministic 2.5D via CSS transforms is fine if reliable headless.
- **Brand kept**: dual‑brand lockup every frame/slide; amber `#FFBE0B` signature; professionally‑dark base; co‑branded Build/Growth fix; CTA contains `DM "AUDIT"`; one concrete number; contrarian hook.
- **Performance**: ~1000+ video frames at ~1.7 fps on the owner's machine — keep per‑frame cost sane (avoid full‑screen per‑frame blur, thousands of nodes). Carousel is 5 stills (can be heavier).
- **Legibility & safe zones** for sound‑off vertical social.

If a desirable technique can't be done deterministically/offline, say so and give the closest compliant alternative.

---

## Step 3 — Produce these deliverables (this is the required output)

Structure your answer in these sections. Be specific and buildable. Where helpful, include **ready‑to‑use deterministic CSS/SVG/JS snippets** (functions of `t`, with the seed‑derived constants shown as placeholders).

### A. The Generative Design‑System Blueprint (the core ask)
Define the **independent, seeded design axes** that combine into a fresh daily look, e.g.:
`palette · color‑grade · type‑pairing · type‑scale · grid/composition archetype · motion personality · transition family · background field/world · texture/material · accent treatment · icon treatment`.
For each axis: the **option set** (concrete named variants), how the **seed selects + anti‑repeats** it, and the **coherence rules** that keep any combination on‑brand and senior‑grade (so combinations never look random or clash). Show how this plugs into the existing seed model and `apex_art.choose_look` / `apex_lush` palette selection. Aim for **thousands of distinct, tasteful combinations**, not 6×4.

### B. Typography system
Concrete pairings from the available fonts (+ any free OFL additions to fetch), a modular type scale + vertical rhythm, hierarchy rules (kicker/tag/headline/punch/sub/chips/CTA/lockup), tracking/case/optical rules per pairing, and **kinetic‑type techniques** (deterministic) for the video headline and per‑day "type personalities."

### C. Color & material system
Seeded **dark premium** palette recipes (base + 2–3 tonal grades + the fixed amber + 1 optional secondary accent with harmony rules), gradient‑mesh grading, duotone/glass/glow treatments, and a **texture/material layer** (grain/noise/shadow/light‑leak) — all as CSS/SVG with legibility guarantees on dark.

### D. Layout & composition library
A set of **composition archetypes** (e.g. centered‑hero, left‑editorial, asymmetric, split, full‑bleed‑type, lower‑third, grid) as concrete CSS layouts that keep the lockup + safe zones, plus rules for which archetypes suit which beat (hook vs data vs fix vs CTA) and how the seed varies placement per scene without breaking legibility.

### E. Motion & transition system (deterministic)
A **library of `render(t)` motion primitives** (staggered reveal, mask/`clip-path` wipe, SVG line‑draw, number ticker, parallax layers, scale/blur‑in, character/word cascade, accent flashes) with easing functions, plus **per‑day motion personalities** that pick & tune these. Include the math/snippets as pure functions of `t`, and note per‑frame cost.

### F. Deterministic data‑viz vocabulary
SVG/CSS mini‑charts (animated bar/line/donut/gauge/comparison‑meter/number‑ticker) drawn from the post's single number, with reveal animations — so the "Problem/Peak" beats carry credible, moving data.

### G. Per‑deliverable polish
Specific upgrades for the **carousel** (5 stills as one art‑directed set; cover/hook slide craft; swipe affordance; per‑slide composition variety) and the **video** (first‑2s hook, beat pacing, exit/enter craft, end‑card/CTA, sound‑off legibility), keeping carousel↔video as one campaign.

### H. Quality rubric + self‑grading
Define a concise **rubric that separates amateur/AI‑template work from 15‑year senior work** (hierarchy, restraint, rhythm, contrast, intentionality, finish, cohesion, surprise). Then **grade the current system** (per the context) and **grade your proposed system** against it, honestly.

### I. Prioritized implementation roadmap (for the coding agent)
A ranked backlog (highest design‑ROI first), each item with: **what**, **why it elevates craft**, **exact deterministic implementation** (CSS/SVG/JS pattern), **file/function to change** (use the file map in the context), **how it increases daily variety**, **perf note**, and a **way to verify** (e.g. an assertion or a visual check). Group into phases so it can ship incrementally.

### J. Optional spec/schema extensions
Any **new optional `day_spec` fields** or **art‑direction knobs** needed (kept lenient/back‑compatible per `apex_spec.validate`), and any updates the local generator (`apex_concept.py`) and the GPT authoring prompt should make to drive the new system.

---

## Output format rules
- Lead with a one‑paragraph executive summary, then the sections A–J above, then a final **"if you only build 5 things"** shortlist.
- Be concrete: name variants, give numbers, show snippets. Prefer tables for option sets and the roadmap.
- Every technique must be tagged **[deterministic ✓]** with a one‑line note on how it stays a pure function of `t` (or marked **[carousel‑only]** if it's a still‑image technique).
- Assume the reader is an expert coding agent — be technical, skip basics, cite files/functions.
- Do **not** propose anything paid, Node‑based, WebGL‑dependent, network‑at‑render, or that breaks the brand rules. If tempted, give the offline/deterministic equivalent instead.

## The bar
Every daily post should make a founder stop scrolling and think *"a senior studio made this for me today"* — and a designer who saw yesterday's post should not be able to guess today's. Design the **system** that guarantees both, within these constraints.
