# -*- coding: utf-8 -*-
"""
Apex Studio smoke tests — fast, offline, no Chrome required.

Covers the pure logic that the daily pipeline depends on: the local concept
generator, the day_spec validator, the lush HTML builders, and HTML-level
determinism. (Frame-level pixel determinism is NOT guaranteed for the lush look —
the glass backdrop-filter blur composites through SwiftShader and jitters sub-pixel;
each frame is rendered once per pass, so the video is unaffected. We assert the
*HTML* is byte-identical, which is the meaningful guarantee.)

Run standalone (no pytest needed):   python tests/smoke.py
Or under pytest if installed:         pytest tests/smoke.py
"""
import os, sys, json, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import apex_concept
import apex_spec


def test_generate_is_valid():
    for _ in range(5):
        spec = apex_concept.generate()
        ok, errs = apex_spec.validate(spec)
        assert ok, f"generated spec invalid: {errs}"


def test_generate_varies():
    pillars = [apex_concept.generate()["id"].rsplit("_", 1)[0] for _ in range(6)]
    assert len(set(pillars)) >= 3, f"anti-repeat too weak, only saw {set(pillars)}"


def test_validate_rejects_wrong_slide_count():
    spec = apex_concept.generate()
    spec["carousel"]["slides"] = spec["carousel"]["slides"][:4]
    ok, errs = apex_spec.validate(spec)
    assert not ok and any("exactly 5" in e for e in errs), errs


def test_validate_rejects_too_many_li_tags():
    spec = apex_concept.generate()
    spec["carousel"]["linkedin"]["hashtags"] = ["a", "b", "c", "d"]
    ok, errs = apex_spec.validate(spec)
    assert not ok and any("<= 3" in e for e in errs), errs


def test_validate_rejects_bad_mood():
    spec = apex_concept.generate()
    spec["video"]["music_mood"] = "party"
    ok, errs = apex_spec.validate(spec)
    assert not ok and any("music_mood" in e for e in errs), errs


def test_carousel_captions():
    spec = apex_concept.generate()
    li, fb = apex_spec.carousel_captions(spec["carousel"])
    assert li.strip() and fb.strip(), "empty captions"
    assert "AUDIT" in (li + fb).upper(), "CTA 'AUDIT' missing from captions"
    assert li.endswith("\n") and fb.endswith("\n")


def test_lush_slide_html_markers():
    import apex_lush
    spec = apex_concept.generate()
    slide = spec["carousel"]["slides"][0]
    html = apex_lush.build_lush_slide_html(slide, 1, 5, spec["carousel"]["kicker"], seed=7)
    for marker in ('class="scene"', 'class="lock"', "APEX IT SOLUTIONS", "APEX MARKETINGS", 'class="dind"'):
        assert marker in html, f"missing {marker} in lush slide html"
    import re
    words = re.findall(r"[A-Za-z]{4,}", slide["headline"][0].replace("**", ""))
    assert words and any(w in html for w in words), "headline text not rendered into slide"


def test_lush_video_html_deterministic():
    import apex_lush
    import build_today_video as V
    spec = apex_concept.generate()
    sp = os.path.join(tempfile.gettempdir(), "apex_smoke_spec.json")
    with open(sp, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False)
    os.environ["APEX_SPEC"] = sp
    concept = V.get_concept()
    tl = V.build_timeline([4.0, 4.5, 3.2, 4.0, 4.6, 3.6], concept.get("look"))
    h1 = apex_lush.build_lush_html("instagram", concept, tl)
    h2 = apex_lush.build_lush_html("instagram", concept, tl)
    assert h1 == h2, "lush video HTML is not deterministic for the same concept"
    assert len(h1) > 2000 and "render(" in h1, "lush video HTML looks malformed"


def test_assets_verify_if_present():
    import fetch_assets
    fonts_m = os.path.join(ROOT, "assets", "fonts", "manifest.json")
    icons_m = os.path.join(ROOT, "assets", "icons", "lucide", "manifest.json")
    if not (os.path.exists(fonts_m) and os.path.exists(icons_m)):
        print("    (skip: assets not fetched in this environment)")
        return
    assert fetch_assets.verify() == 0, "cached assets don't match their manifest"


# ----------------- standalone runner (no pytest dependency) -----------------
def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    # isolate the on-disk pillar memory so tests don't disturb the real rotation
    mem = os.path.join(ROOT, "art_memory.json")
    backup = None
    if os.path.exists(mem):
        with open(mem, "rb") as f:
            backup = f.read()
    npass = 0
    fails = []
    try:
        for t in tests:
            try:
                t()
                print(f"  PASS  {t.__name__}")
                npass += 1
            except Exception as ex:
                print(f"  FAIL  {t.__name__}: {ex}")
                fails.append(t.__name__)
    finally:
        if backup is not None:
            with open(mem, "wb") as f:
                f.write(backup)
    print(f"\n{npass}/{len(tests)} passed" + (f", {len(fails)} FAILED: {fails}" if fails else " — all green"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(_run())
