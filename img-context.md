# Apex Daily Social Post — Generation Context & Full Spec

> **Purpose of this file.** Hand this file **plus the whole `C:\xampp\htdocs\apexsocialmedia` folder** to any AI/tool and say *"generate a post for today."* This document contains everything needed to produce the post correctly: the brands, the voice, the exact design system, the file layout, the rendering pipeline, and a step‑by‑step procedure. Follow it literally. When in doubt, change **words only** and keep the **design system, colors, layout, and file structure** exactly as specified.
>
> **Companion spec:** there is also a **`video-context.md`** for the animated **video** post ("create a video for today" → `build_today_video.py`). It reuses this image design system. Read it for video; this file owns the brand, voice, content, and the image carousel.

---

## 0. QUICKSTART — "generate a post for today"

The post is produced by one script: **`build_today_pack.py`** (repo root). It renders a **5‑slide carousel** in **two themes** (dark + light) for **two platforms** (LinkedIn + Facebook/Instagram) and writes them into `generated_images/`, plus two caption files. You do **not** hand-place pixels — you edit a few **content variables** and run the script.

To make today's post:

1. **Pick today's angle** (one idea, contrarian, proof‑led — see §4 and §10).
2. **Write the on‑graphic text** for the 5 slides → edit the `SLIDES` list and the `kicker` string in `build_today_pack.py` (§7, §10).
3. **Write the two captions** → edit `LINKEDIN_CAPTION` and `FB_CAPTION` (§8).
4. **Render:** run `python build_today_pack.py`.
5. **Verify** (§14): every slide is `1080×1350` RGB; `generated_images/` holds exactly the 4 folders + `linkedin.md` + `fb.md`; re‑open the PNGs and re‑check dimensions (a second agent sometimes overwrites this folder — see §14).

Do **not** change the palette, fonts, layout, texture, logo choices, dimensions, or folder names unless the human explicitly asks. Those are the brand system.

---

## 1. What this project is

A daily, **co‑branded** social media post for two sister companies that are always presented together: **Apex IT Solutions × Apex Marketings**. The post is an educational, scroll‑stopping **carousel** (multi‑image, swipeable) plus a caption. It is *not* a "we offer services" advert — it teaches one sharp lesson and ends with a soft call to action (`DM "AUDIT"`).

The combined thesis of every post: **"Build the system. Turn it into demand."** Apex IT builds the system; Apex Marketings turns it into demand.

---

## 2. The two brands

| | **Apex IT Solutions** | **Apex Marketings** |
|---|---|---|
| Role | The **BUILD** brand — technology / engineering | The **GROWTH / REVENUE** brand — marketing |
| Owns | custom software, web & mobile apps, DevOps, cloud, automation, performance, technical CRO/build | SEO, Google Ads, Meta Ads, social media, e‑commerce growth, lead generation, branding, CRO campaigns |
| Logo mark | a sharp **arrow** | a stylised **"M"** |
| Brand color in this system | **ink `#171717`** (the neutral axis; shown off‑white on dark) | **amber `#FFBE0B`** (the single accent; deepened to bronze on light) |
| Axis word on graphics | **BUILD** | **GROWTH** |

Cross‑promote only when the topic naturally bridges build → growth or growth → build. Both logos appear together in every slide's footer lockup.

---

## 3. Audience & market

- **Who:** business owners, founders, and marketing leads.
- **Where:** Pakistan (currency **Rs**, **WhatsApp**‑driven lead handling) **and** international B2B.
- **What they value:** concrete proof, real lessons, sharp opinions — not jargon, not hype.
- A single serious inquiry beats 500 low‑quality likes. Optimize for **saves, shares, comments, and DMs**, not vanity likes.

---

## 4. Brand voice & copywriting rules

**Voice:** direct, proof‑led, contrarian, zero fluff. Turn services into **problems the reader feels**. Teach a lesson; don't pitch. Sound human, not corporate.

**Turn services into problems** (the core move):
- ❌ "We offer web development." → ✅ "Your homepage should answer 5 questions in 10 seconds."
- ❌ "We offer SEO." → ✅ "Posting blogs without search intent isn't SEO. It's just publishing."
- ❌ "We offer DevOps." → ✅ "If your developer manually uploads files to the server, you don't have a deployment process."

**Hooks** (first line must stop the scroll and invert a belief):
- "Your website isn't slow because of images. It's slow because nobody planned performance before development."
- "Your lead didn't die. It waited."
- "Ads rent attention. SEO owns it."

**Primary CTA:** always conversational — `DM "AUDIT"` (offer a free audit). Never "hire us."

---

## 5. The deliverable — exact output

Everything lands in **`C:\xampp\htdocs\apexsocialmedia\generated_images\`**. The **image carousel** owns exactly these 6 items:

```
generated_images/
├─ linkedin-dark/    01.png 02.png 03.png 04.png 05.png
├─ linkedin-light/   01.png 02.png 03.png 04.png 05.png
├─ fb-dark/          01.png 02.png 03.png 04.png 05.png
├─ fb-light/         01.png 02.png 03.png 04.png 05.png
├─ linkedin.md       (LinkedIn caption — copy‑paste ready)
└─ fb.md             (Facebook/Instagram caption — copy‑paste ready)
└─ video/            (OPTIONAL — only if the video pipeline ran; see video-context.md)
└─ video.md          (OPTIONAL — daily video caption, sibling to linkedin.md/fb.md)
```
The `video/` subfolder (instagram_reel.mp4 + linkedin_video.mp4) and the top‑level `video.md` caption are produced by `build_today_video.py` and are **allowed to coexist**. `cleanup_output()`'s whitelist includes `"video"` (KEEP_DIRS) and `"video.md"` (KEEP_FILES), so the image run will NOT delete them. Apart from those, the carousel folder still holds exactly the 6 items above.

- **Image size:** every slide is **1080 × 1350 px** (4:5 portrait — maximum feed real‑estate / reach), PNG, sRGB.
- **20 images total** = 2 themes × 2 platforms × 5 slides.
- **Slides are visually identical across LinkedIn and FB for a given theme.** The only platform difference is the **caption** (`linkedin.md` vs `fb.md`). The visual variable is the **theme** (dark vs light). The script renders 5 slides per theme once and writes them into both platform folders.
- Captions are **short** (the slides carry the substance). LinkedIn ≈ 600–900 chars; FB/IG ≈ 500–800 chars.
- The script's `cleanup_output()` enforces the whitelist (the 6 carousel items **+ the `video/` folder**) — anything else in `generated_images/` is deleted on each run. **Write review/contact sheets to the repo ROOT, never into `generated_images/`.**

---

## 6. The design system (fixed — this is the brand)

**Concept: premium "monochrome + single amber accent."** Near‑black/near‑white canvas, ink/off‑white type, and exactly **one** accent color — amber `#FFBE0B`. This is the Linear/Vercel/Stripe premium aesthetic. Apex IT = the neutral (ink/off‑white); Apex Marketings = the amber. **Never introduce a second accent** (no blue, no gold‑besides‑amber, no purple).

### 6.1 Palette tokens (exact hex — both themes)

These live in `PALETTES` in `build_today_pack.py`. Reproduce exactly if rebuilding.

**DARK theme**
| token | value | use |
|---|---|---|
| base | `#0F1115` | flatten/background base |
| bg_grad | `linear-gradient(168deg,#17181d,#141417 46%,#101218)` | canvas |
| text_primary | `#ECEDF0` | headlines |
| text_secondary | `#AEB3BC` | sublines, labels |
| text_tertiary | `#9398A2` | kicker, separators |
| neutral (Apex IT) | `#ECEDF0` | BUILD dot/lane/chip, off‑white logo arrow |
| amber (Apex Mktgs) | `#FFBE0B` | GROWTH dot/lane/chip, amber logo M, all accents |
| chip_b_border / chip_b_text | `rgba(236,237,240,.34)` / `#D2D5DB` | BUILD chips |
| chip_g_border / chip_g_text | `rgba(255,190,11,.55)` / `#FFD98A` | GROWTH chips |
| hairline | `#33343A` | rules/dividers |
| bracket | `rgba(255,255,255,.16)` | corner brackets |
| logos | `__ARROW_OFFWHITE__` + `__M_AMBER_BRAND__` | footer lockup |

**LIGHT theme**
| token | value | use |
|---|---|---|
| base | `#F7F8FA` | flatten/background base |
| bg_grad | `linear-gradient(168deg,#FFFFFF,#F6F7FA 46%,#EEF0F4)` | canvas |
| text_primary | `#161616` | headlines |
| text_secondary | `#454B55` | sublines, labels |
| text_tertiary | `#5C636E` | kicker, separators |
| neutral (Apex IT) | `#171717` | BUILD dot/lane/chip, ink logo arrow |
| amber (Apex Mktgs) | `#B5791A` (deepened) | GROWTH dot/lane/border; bright `#FFBE0B` is illegible on white, so it is deepened to `#B5791A` for lines and `#8A5C12` for text |
| chip_b_border / chip_b_text | `rgba(23,23,23,.24)` / `#171717` | BUILD chips |
| chip_g_border / chip_g_text | `rgba(181,121,26,.5)` / `#8A5C12` | GROWTH chips |
| hairline | `#DDE0E6` | rules/dividers |
| bracket | `rgba(23,23,23,.18)` | corner brackets |
| logos | `__ARROW_INK17__` + `__M_INK17__` | footer lockup (both ink — gold/amber M is weak on white) |

### 6.2 Typography

- **Font stack:** `'Segoe UI','Inter',Arial,sans-serif`. Headless Chrome on Windows renders **Segoe UI** (a clean humanist grotesk; bold = `segoeuib.ttf`). **No web fonts / no `@font-face`** — rendering is offline.
- Hierarchy via **size + weight only**, no decoration.
- **Font sizes (current, tuned for readability — keep at least these):**
  - Hero headline `.hxl` **84px** / weight 800 / line‑height 1.0 / letter‑spacing −2.2px
  - Large headline `.hlg` **58px** / 800 / 1.04 / −1.4px
  - Subline `.sub` **28px** / 400 / 1.5
  - Kicker `.kicker` **15px** / 700 / tracking 4px / uppercase
  - Tag (e.g. "THE LEAK") `.tag` **15px** / 800 / amber
  - BUILD/GROWTH label `.lab` **25px** / 800
  - Brand name under label `.brand` **16px** / secondary
  - Chips `.chip` **15px** / 700, padding 12×18, border 1px
  - CTA box `.ctabox` **28px**, Footer brand names `.bname` **17px**
  - Amber emphasis: wrap a word in `<b>` inside a headline → it renders amber.

### 6.3 Background texture (required on BOTH themes — do not remove)

Nine stacked, tasteful layers behind the content (`z-index` of content is 3, so text stays crisp on top). All sit below the foreground; the last four are gated by a single `BG_INTENSITY` knob (default 1.0 = subtle; 0 = off) via `bgop()`:
1. **Film grain** — inline SVG `feTurbulence` (`GRAIN` data‑URI), `mix-blend-mode:overlay`, opacity **.06 dark / .035 light**.
2. **Dot‑grid** — `radial-gradient` dots, `background-size:32px`, color `rgba(255,255,255,.04)` dark / `rgba(23,23,23,.045)` light.
3. **Ambient glow** — amber radial `radial-gradient(760px 620px at 50% 38%, rgba(255,190,11,.10), transparent 62%)`.
4. **Concentric "signal" rings** — centered dashed SVG circles (radii 150/250/360/470/515; one amber ring at 360), faint. Thematic "ping/radar" depth.
5. **Corner brackets** — four 32px L‑shaped hairline brackets framing the canvas.
6. **Gradient‑mesh depth** (`.mesh`) — two soft, offset neutral‑slate radial pools (top‑left + bottom‑right, away from the amber glow) for painterly dimension; ~.07–.10 dark / ~.03–.045 light. Token `mesh`.
7. **Edge vignette** (`.vignette`) — radial that darkens the outer ~36% (`rgba(0,0,0,.05)` dark / `rgba(23,23,23,.03)` light); editorial depth‑frame. Token `vignette`.
8. **Blueprint guides + ruler ticks** (`guides(P)` → `.guides`, z‑index 2) — faint safe‑margin frame, a **center axis broken across the headline band** (gap y≈432→918), and small ruler ticks on a 90px grid along the top/bottom inner edges (extend the corner brackets). Tokens `guide` (lines) / `tick` (ticks).
9. **Ghost slide numeral** (`ghost_glyph(P, idx)` → `.ghost`) — oversized `01..05` (≈540px) bled off the bottom‑right corner, `rgba(255,255,255,.037)` dark / `rgba(23,23,23,.035)` light; quiet per‑slide identity behind the footer lockup.

DOM order inside `.canvas`: grain, dots, glow, `rings_svg`, corner brackets, `.mesh`, `.vignette`, `ghost_glyph`, `guides`. Do not add halftone / hard contour / cross‑hatch / scanlines on top — one structural line‑system (brackets + rings + guides) is the ceiling.

### 6.4 Layout anatomy (every slide, centered & symmetric)

Canvas `1080×1350`, padding `70 78 62`, vertical layout `space-between`, fully **center‑aligned** (mirror‑symmetric):
- **Top (`.head`):** centered **kicker** (the topic system name, uppercase) + a 120px **split‑bar** (left half neutral, right half amber = the two brands).
- **Middle (`.body`, vertically centered):** the slide's content (headline + optional subline + optional motif/columns/CTA).
- **Bottom (`.foot`):** a **5‑dot carousel indicator** (active slide = elongated amber pill) + a centered **footer lockup**: `[arrow] APEX IT SOLUTIONS  ×  APEX MARKETINGS [M]`.

Everything is centered. Do not left‑align. Keep critical content within the corner brackets (~46–70px safe margin).

---

## 7. The carousel format — 5‑slide narrative

The slide **structure is reusable for almost any Apex topic**; only the words change. Order:

1. **COVER** — the hook. Big `.hxl` headline (3 short lines) + one `.sub` line + a `Swipe →` cue. (Optional thematic motif, e.g. a timestamp `9:11 PM → 10:40 AM` for a speed topic.)
2. **PROBLEM** — name the pain concretely. A `.tag` ("THE LEAK"), an `.hlg` headline, a `.sub`, and an optional **motif** (e.g. the meter bar). Make the reader feel the cost.
3. **REFRAME** — the contrarian insight, as a big `.hxl` quote. ("You don't have a lead problem. You have a response‑time problem.") + one supporting `.sub`.
4. **SYSTEM** — the fix, shown as the **BUILD / GROWTH split** (the co‑brand proof): two columns separated by a hairline divider. Left = **BUILD / Apex IT Solutions** with 2 chips; right = **GROWTH / Apex Marketings** with 2 chips. Chips are 1–3‑word capability labels relevant to the topic.
5. **CTA** — `.hlg` payoff line + `.sub` ("Build the system. Turn it into demand — in that order.") + a `.ctabox` ending in `DM "AUDIT" …, free.`

**On‑graphic text rules:** minimal words per slide. Headlines 3–7 words/line, contrarian, specific. The slides teach; the caption adds depth. Use `<b>…</b>` to make a key word amber. Use `<br>` for deliberate line breaks. HTML entities: `&rsquo; &ldquo; &rdquo; &mdash; &rarr; &nbsp;`.

---

## 8. Captions (`linkedin.md`, `fb.md`)

Two short, copy‑paste‑ready caption files (one per platform; shared across both themes). Structure:

- **Line 1 = the hook** (must survive the mobile "see more" fold, ≈140 chars).
- A `Swipe …` cue (it's a carousel).
- 1–2 short teaching lines (the lesson), naming the BUILD→GROWTH split once.
- The CTA: `DM "AUDIT" …, free.`
- **One open question** on its own line (drives comments — comments are worth ~15× a like in 2026).
- Hashtags on the final line.

**Hashtag rules:** LinkedIn = **exactly 3** (e.g. `#LeadGeneration #MarketingAutomation #B2BSales`). FB/IG = **8–15**, mix broad + Pakistan‑niche (e.g. `#whatsappbusiness #smallbusinesspakistan #founders #speedtolead …`).

**Length:** LinkedIn ≈ 600–900 chars (kept short because the carousel carries the substance). FB/IG ≈ 500–800 chars, slightly snappier, may use one tasteful emoji, add `Save this`.

---

## 9. Rendering pipeline — how `build_today_pack.py` works

**Environment (verified):** Windows 11; Python **3.12** + **Pillow 10.1**; Google **Chrome** headless at `C:\Program Files\Google\Chrome\Application\chrome.exe`. No Playwright/imgkit/Node required.

**Flow per slide:**
1. `doc(theme, idx, total, inner)` builds a full self‑contained HTML document (all CSS inline, colors pulled from `PALETTES[theme]`).
2. Logos are referenced as `__TOKEN__` placeholders; `inject()` replaces each with a base64 data‑URI built by `token_map()` from every PNG in `logos/variants/`.
3. Chrome screenshots the HTML at **2× device scale** (`--force-device-scale-factor=2 --window-size=1080,1350 --screenshot=… --headless --hide-scrollbars`).
4. **Light‑theme flatten fix (critical):** the capture is opened as RGBA and **composited onto the theme `base` color** (`#F7F8FA` light / `#0F1115` dark) *before* `convert("RGB")`. The transparent‑bg flag otherwise flattens light edges to **black**. Then LANCZOS‑downscale to `1080×1350`.
5. `__main__` loops `theme ∈ {dark,light}`, renders the 5 `SLIDES`, and writes them into both `linkedin-{theme}/` and `fb-{theme}/` as `01.png … 05.png`; writes the two captions; runs `cleanup_output()`.

**Run it:**
```bash
cd C:\xampp\htdocs\apexsocialmedia
python build_today_pack.py
```
Expected: `wrote linkedin-dark/ (5 slides)` ×4, then `DONE. generated_images now holds: ['fb-dark', 'fb-light', 'fb.md', 'linkedin-dark', 'linkedin-light', 'linkedin.md']`.

---

## 10. HOW TO GENERATE A NEW POST FOR TODAY (do this)

**Keep the design, structure, pipeline, colors, fonts, and file layout exactly. Change only the words.** Edit these variables in `build_today_pack.py`:

1. **`kicker`** (inside `doc()`, currently `"Speed-to-Lead System"`): a 2–4‑word uppercase "system name" for today's topic (e.g. `"Conversion System"`, `"Search Authority System"`).

2. **`SLIDES`** (list of 5 HTML strings) — rewrite the words for today's angle, keeping each slide's *shape*:
   - Slide 1: `.stamp` (optional motif) + `.hxl` hook + `.sub` + `.swipe`.
   - Slide 2: `.tag` + `.hlg` problem + `.sub` + optional `.meter` motif (only if a "from X → to Y" number fits; otherwise drop the meter).
   - Slide 3: `.hxl` reframe + `.sub`.
   - Slide 4: `.tag` + `.hlg` + the `.split` with **2 Apex‑IT chips** (BUILD) and **2 Apex‑Marketings chips** (GROWTH) relevant to the topic.
   - Slide 5: `.hlg` payoff + `.sub` + `.ctabox` with `DM "AUDIT" …, free.`
   - The motif on slides 1–2 (timestamp + meter) is **speed‑specific** — for other topics, replace with a topic‑relevant number/motif or omit it (the layout still works).

3. **`LINKEDIN_CAPTION`** and **`FB_CAPTION`** — rewrite per §8 (short, hook‑first, one open question, correct hashtag counts).

4. **Run** `python build_today_pack.py` and **verify** (§14).

**Choosing today's angle** — pick ONE, make it contrarian and specific (content pillars: *proof, authority, process, human trust, conversion*). Good fresh angles for Apex:
- A slow/fragile website silently burns leads (speed, mobile, uptime) — Apex IT.
- "Cheap website now = expensive later" (Rs framing) — founder lesson.
- Ads rent attention; SEO + a strong site own it — Apex Marketings.
- Speed‑to‑lead / follow‑up automation (the current post).
- Build‑to‑demand: a great product with no distribution, or great ads on a weak system — both fail.
- A homepage that doesn't answer the buyer's 5 questions in 10 seconds.

Do not reuse the exact same angle two days running.

---

## 11. Hard rules / do‑NOT list

- **One accent only** (amber). Never add a second accent color.
- **Dark + light both required**, both textured. 4:5 (1080×1350) only.
- **Minimal on‑graphic text** — headline + tiny subline + a few chips. The caption teaches.
- **No AI/robot/glowing‑brain/hologram/circuit clichés.** Type + grid + texture are the visuals.
- **Never invent fake client names, logos, results, or case studies.** Use general truths and self‑audit framing.
- **≤3 hashtags on LinkedIn**; 8–15 on FB/IG.
- **No outbound link in a LinkedIn post body** (suppresses reach) — put links in the first comment.
- **Both logos** appear together every slide; don't merge or restyle the marks.
- Keep `generated_images/` to exactly the 6 items; write scratch files to repo ROOT.
- Don't make every line a sales pitch; sound human.

---

## 12. Reach / algorithm tactics (2026, applied)

- **Carousel** (multi‑image) outperforms a single dense image — one idea per slide → more dwell + saves.
- **Hook before the fold** (first ~140 chars) in both the cover slide and the caption line 1.
- **End the caption with ONE open question** (comments ≈ 15× a like).
- **Post LinkedIn from a founder/personal profile**, then reshare from the Company Page; reply to comments in the first 15–30 min.
- FB/IG reward **saves + shares** → add "Save this," keep it skimmable.
- 4:5 portrait maximizes mobile feed real‑estate.

---

## 13. Asset inventory

**Source logos** (`logos/`): `apexit.png` (ink arrow), `apex_it_arrow_white.png` (white arrow), `apexmarketings.png` / `apex_marketings_m_gold.png` (gold M), `apex_marketings_m_white.png`.

**Recolored variants** (`logos/variants/`, consumed as `__NAME__` tokens) — arrow + M each in: `WHITE, OFFWHITE, PLATINUM, INK, INK17, BLUE, ELECTRIC, GOLD, AMBER` plus `M_AUTHGOLD`, `M_AMBER_BRAND`. **This system uses:** dark → `ARROW_OFFWHITE` + `M_AMBER_BRAND`; light → `ARROW_INK17` + `M_INK17`.
To make a new color variant, alpha‑fill the source mark's alpha channel with the target RGB (recipe in `fix_text.py`; the existing variants were built this way), e.g.:
```python
from PIL import Image; import numpy as np, os
LOGO=r"C:\xampp\htdocs\apexsocialmedia\logos"; VAR=os.path.join(LOGO,"variants")
a=np.array(Image.open(os.path.join(LOGO,"apex_it_arrow_white.png")).convert("RGBA"))[:,:,3]
h,w=a.shape; out=np.zeros((h,w,4),np.uint8); out[:,:,0:3]=(23,23,23); out[:,:,3]=a
Image.fromarray(out,"RGBA").save(os.path.join(VAR,"ARROW_INK17.png"))
```

**Fonts:** Segoe UI family is installed (`segoeui.ttf`, bold `segoeuib.ttf`). Used directly by Chrome.

---

## 14. Verification & gotchas

After every run:
1. **Dimensions:** each of the 20 PNGs is `1080×1350`, mode `RGB`.
2. **Folder invariant:** `generated_images/` contains exactly `linkedin-dark, linkedin-light, fb-dark, fb-light, linkedin.md, fb.md`; each image folder has exactly 5 slides.
3. **Concurrent‑agent overwrite (important):** another tool on this machine (a Gemini/Antigravity IDE agent under `C:\Users\…\.gemini\antigravity-ide\…`) sometimes writes into `generated_images/` and can overwrite freshly rendered files. **Re‑open the PNGs a few seconds after writing and re‑check size/content**; re‑render any that drifted. If they keep getting clobbered, tell the human to pause the other agent.
4. **Light‑theme black edges** → you skipped the composite‑onto‑base step (§9.4).
5. **`WARNING leftover tokens`** in output → a logo `__TOKEN__` had no matching PNG in `logos/variants/`; fix the token name or create the variant.
6. Keep contact/review sheets **out** of `generated_images/` (cleanup deletes non‑whitelist files anyway).

Quick check script:
```python
import os
from PIL import Image
OUT=r"C:\xampp\htdocs\apexsocialmedia\generated_images"
for d in ["linkedin-dark","linkedin-light","fb-dark","fb-light"]:
    n=sorted(os.listdir(os.path.join(OUT,d)))
    sz={Image.open(os.path.join(OUT,d,x)).size for x in n}
    print(d, len(n), sz)   # expect 5 {(1080,1350)}
print(sorted(os.listdir(OUT)))
```

---

## 15. Reference — the current post (worked example)

**Topic:** speed‑to‑lead / follow‑up. **kicker:** `Speed-to-Lead System`.
**Slides:**
1. Cover — motif `9:11 PM → 10:40 AM`; headline *"Your lead didn't die. It waited."*; sub *"Most deals are lost in the silence between the click and your reply."*; `Swipe →`.
2. Problem — tag *THE LEAK*; *"A buyer messaged at 9:11 PM. You replied at 10:40 AM."*; meter `13 hrs late → 5 min`.
3. Reframe — *"You don't have a lead problem. You have a response‑time problem."*
4. System — tag *THE FIX*; *"Speed isn't a trait. It's a system."*; BUILD (Apex IT): `Instant reply`, `One inbox`; GROWTH (Apex Marketings): `Follow-up cadence`, `Reply in minutes`.
5. CTA — *"Reply in minutes, not hours."*; *"Build the system. Turn it into demand — in that order."*; *DM "AUDIT" and we'll map your speed‑to‑lead, free.*

**LinkedIn caption** (3 hashtags) and **FB caption** (10 hashtags) are the current `linkedin.md` / `fb.md` and the `LINKEDIN_CAPTION` / `FB_CAPTION` constants in `build_today_pack.py` — use them as the tone/length template for new posts.

---

*End of spec. To produce today's post: edit `kicker`, `SLIDES`, `LINKEDIN_CAPTION`, `FB_CAPTION` in `build_today_pack.py`, run it, verify. Keep the design system identical.*
