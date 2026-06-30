# -*- coding: utf-8 -*-
"""Fetch open assets for Apex Studio Design Engine v2.

The renderer never uses the network. This script is the explicit, idempotent
asset refresh step: Google Fonts WOFF2 files and Lucide SVG icons are cached in
assets/ with source/license/hash metadata.
"""
import datetime as _dt
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(ROOT, "assets", "fonts")
ICON_DIR = os.path.join(ROOT, "assets", "icons", "lucide")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 ApexStudioAssetFetcher/2.0"

FONT_CSS = {
    "Archivo": ("https://fonts.googleapis.com/css2?family=Archivo:wght@400;700;800;900&display=swap", "SIL OFL 1.1"),
    "Inter": ("https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap", "SIL OFL 1.1"),
    "Sora": ("https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap", "SIL OFL 1.1"),
    "Space Grotesk": ("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap", "SIL OFL 1.1"),
    "Fraunces": ("https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT,WONK@9..144,400..900,50,1&display=swap", "SIL OFL 1.1"),
    "Newsreader": ("https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400..800&display=swap", "SIL OFL 1.1"),
    "Syne": ("https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&display=swap", "SIL OFL 1.1"),
    "Manrope": ("https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap", "SIL OFL 1.1"),
    "Bricolage Grotesque": ("https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&display=swap", "SIL OFL 1.1"),
    "Geist": ("https://fonts.googleapis.com/css2?family=Geist:wght@400;600;700;800;900&display=swap", "SIL OFL 1.1"),
}

LUCIDE_ICONS = [
    "activity", "alarm-clock", "arrow-up-right", "badge-check", "chart-bar", "blocks",
    "bot", "brain-circuit", "calendar", "chart-no-axes-combined", "circle-check",
    "chevrons-up", "circle-dollar-sign", "cloud", "code", "coins", "cpu", "mouse-pointer-click",
    "database", "funnel", "gauge", "globe", "hourglass", "layers", "chart-line",
    "link", "lock-keyhole", "magnet", "megaphone", "mouse-pointer-click", "network",
    "panel-top", "radar", "rocket", "scan-search", "search", "send", "server",
    "shield-check", "shopping-cart", "signal", "smartphone", "sparkles", "square-code",
    "target", "timer", "trending-up", "workflow", "zap",
]
LUCIDE_URL = "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/{name}.svg"

def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def _sha(data):
    return hashlib.sha256(data).hexdigest()

def _safe_name(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def fetch_fonts():
    os.makedirs(FONT_DIR, exist_ok=True)
    entries = []
    for family, (css_url, license_name) in FONT_CSS.items():
        try:
            css = _get(css_url).decode("utf-8", "replace")
        except Exception as ex:
            print(f"font css failed: {family}: {ex}")
            continue
        blocks = re.findall(r"@font-face\s*{(.*?)}", css, flags=re.S)
        seen = set()
        count = 0
        for i, block in enumerate(blocks):
            mu = re.search(r"url\((https://[^)]+?\.(?:woff2|ttf)[^)]*)\)\s*format\('?(woff2|truetype)'?\)", block)
            if not mu:
                continue
            url = mu.group(1); fmt = mu.group(2)
            if url in seen:
                continue
            seen.add(url)
            parsed = urllib.parse.urlparse(url)
            ext = os.path.splitext(parsed.path)[1].lstrip(".") or ("ttf" if fmt == "truetype" else "woff2")
            suffix = os.path.basename(parsed.path).split(".")[0][-10:]
            fname = f"{_safe_name(family)}-{i:02d}-{suffix}.{ext}"
            path = os.path.join(FONT_DIR, fname)
            if os.path.exists(path):
                data = open(path, "rb").read()
            else:
                data = _get(url)
                with open(path, "wb") as f:
                    f.write(data)
            def prop(name, default="normal"):
                mm = re.search(name + r"\s*:\s*([^;]+);", block)
                return (mm.group(1).strip() if mm else default)
            entries.append({
                "family": family,
                "file": fname,
                "source": url,
                "css_source": css_url,
                "license": license_name,
                "format": "truetype" if fmt == "truetype" else "woff2",
                "weight": prop("font-weight", "400"),
                "style": prop("font-style", "normal"),
                "stretch": prop("font-stretch", "normal"),
                "unicode_range": prop("unicode-range", ""),
                "sha256": _sha(data),
            })
            count += 1
        print(f"fonts: {family} -> {count} files")
    _write_manifest(FONT_DIR, entries)
    return entries

def fetch_icons():
    os.makedirs(ICON_DIR, exist_ok=True)
    entries = []
    for name in LUCIDE_ICONS:
        url = LUCIDE_URL.format(name=name)
        fname = f"{name}.svg"
        path = os.path.join(ICON_DIR, fname)
        try:
            if os.path.exists(path):
                data = open(path, "rb").read()
            else:
                data = _get(url)
                with open(path, "wb") as f:
                    f.write(data)
            entries.append({
                "name": name,
                "file": fname,
                "source": url,
                "license": "ISC",
                "sha256": _sha(data),
            })
        except Exception as ex:
            print(f"icon failed: {name}: {ex}")
    print(f"icons: lucide -> {len(entries)} files")
    _write_manifest(ICON_DIR, entries)
    return entries

def _write_manifest(folder, entries):
    manifest = {
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "entries": entries,
    }
    with open(os.path.join(folder, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

def verify():
    """Re-hash every cached asset against its manifest. Offline; no network.
    Returns 0 when all present + matching, else 1 (usable as a CI/smoke gate)."""
    problems = 0
    for folder, label in ((FONT_DIR, "fonts"), (ICON_DIR, "icons")):
        mpath = os.path.join(folder, "manifest.json")
        if not os.path.exists(mpath):
            print(f"verify {label}: NO MANIFEST ({mpath}) — run `fetch_assets.py` first")
            problems += 1
            continue
        entries = (json.load(open(mpath, encoding="utf-8")) or {}).get("entries", [])
        ok = miss = bad = 0
        for e in entries:
            p = os.path.join(folder, e.get("file", ""))
            if not os.path.exists(p):
                miss += 1; problems += 1; print(f"  MISSING  {label}/{e.get('file')}")
            elif _sha(open(p, "rb").read()) != e.get("sha256"):
                bad += 1; problems += 1; print(f"  MISMATCH {label}/{e.get('file')}")
            else:
                ok += 1
        print(f"verify {label}: {ok} ok, {miss} missing, {bad} mismatch ({len(entries)} in manifest)")
    print("VERIFY OK" if problems == 0 else f"VERIFY FAILED: {problems} problem(s)")
    return 0 if problems == 0 else 1

AUDIO_MOODS = ["driving", "uplift", "tense"]
AUDIO_README = (
    "Apex Studio — real audio (optional). Drop CC0 / royalty-free (commercial-OK) files here;\n"
    "the renderer auto-picks them (seeded per post) and falls back to the built-in procedural\n"
    "engine when a folder is empty. So this is purely an upgrade — nothing breaks if left empty.\n\n"
    "MUSIC  ->  assets/music/<mood>/*.mp3|wav     moods: driving, uplift, tense\n"
    "   Free CC0 sources: Pixabay Music (https://pixabay.com/music/ — no attribution, commercial OK),\n"
    "   Free Music Archive (https://freemusicarchive.org/ — filter to CC0).\n"
    "   ~6-10 tracks per mood gives strong daily variety.\n\n"
    "SFX    ->  assets/sfx/<name>*.wav|mp3         names: whoosh, riser, tick, thud, chime, impact\n"
    "   Free CC0 sources: Pixabay SFX (https://pixabay.com/sound-effects/), ZapSplat (CC0 1.0).\n"
)
def scaffold_audio():
    import glob
    base_m = os.path.join(ROOT, "assets", "music"); base_s = os.path.join(ROOT, "assets", "sfx")
    for m in AUDIO_MOODS:
        os.makedirs(os.path.join(base_m, m), exist_ok=True)
    os.makedirs(base_s, exist_ok=True)
    with open(os.path.join(ROOT, "assets", "AUDIO_README.txt"), "w", encoding="utf-8") as f:
        f.write(AUDIO_README)
    nm = sum(len(glob.glob(os.path.join(base_m, m, "*.*"))) for m in AUDIO_MOODS)
    ns = len(glob.glob(os.path.join(base_s, "*.*")))
    print("audio: scaffolded assets/music/{%s}/ + assets/sfx/ (see assets/AUDIO_README.txt)" % ",".join(AUDIO_MOODS))
    print("  present now: %d music files, %d sfx -> renderer uses them if any, else procedural fallback." % (nm, ns))
    return 0

def main():
    if "--verify" in sys.argv:
        return verify()
    if "--audio" in sys.argv:
        return scaffold_audio()
    dry = "--dry-run" in sys.argv
    print("Apex Studio asset refresh")
    print("fonts:", ", ".join(FONT_CSS))
    print("icons:", len(LUCIDE_ICONS), "Lucide SVGs")
    if dry:
        print("dry-run only")
        return 0
    fonts = fetch_fonts()
    icons = fetch_icons()
    print(f"done: {len(fonts)} font files, {len(icons)} icons")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
