# -*- coding: utf-8 -*-
"""
Apex Studio — make TODAY's full post in ONE command.

Produces the dark "lush" 5-slide carousel AND the narrated vertical video, both
rendered from the SAME day_spec (same concept + seed), so the two halves match.

Usage:
  python build_today.py                  # fresh local concept for today -> writes day_spec.json, builds both
  python build_today.py --spec my.json   # use an existing day_spec (e.g. pasted from GPT)
  python build_today.py --carousel       # carousel only
  python build_today.py --video          # video only
  python build_today.py --field galaxy   # pin the background field (galaxy|bubbles|particles|orbits)
  python build_today.py --classic        # classic (non-lush) look

Env: honours APEX_SPEC (existing file) and APEX_LUSH (default "1" here). Fully offline.
"""
import os, sys, subprocess, datetime, json

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

def _arg(args, name, default=None):
    return args[args.index(name) + 1] if (name in args and args.index(name) + 1 < len(args)) else default

def ensure_spec(args):
    """Resolve the day_spec to build from: explicit --spec, else an existing APEX_SPEC,
    else generate a fresh on-brand concept for today and save it to day_spec.json."""
    spec_path = _arg(args, "--spec") or (os.environ.get("APEX_SPEC") if os.environ.get("APEX_SPEC") and os.path.exists(os.environ["APEX_SPEC"]) else None)
    if spec_path:
        return os.path.abspath(spec_path)
    import apex_concept
    spec = apex_concept.generate(date=datetime.date.today().isoformat())
    spec_path = os.path.join(ROOT, "day_spec.json")
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    print(f"[build_today] fresh concept: {spec['id']}  ({spec['date']})  seed {spec['seed']}", flush=True)
    print(f"[build_today]   topic: {spec['topic']}", flush=True)
    return spec_path

def run(script, env):
    print(f"\n[build_today] === {script} ===", flush=True)
    r = subprocess.run([PY, os.path.join(ROOT, script)], env=env, cwd=ROOT)
    if r.returncode != 0:
        print(f"[build_today] {script} FAILED (exit {r.returncode})", flush=True)
        sys.exit(r.returncode)

def main():
    args = sys.argv[1:]
    do_car = "--video" not in args
    do_vid = "--carousel" not in args
    env = dict(os.environ)
    env["APEX_LUSH"] = "" if "--classic" in args else env.get("APEX_LUSH", "1")
    fld = _arg(args, "--field")
    if fld:
        env["APEX_FIELD"] = fld
    env["APEX_SPEC"] = ensure_spec(args)
    print(f"[build_today] spec={env['APEX_SPEC']}  lush={'1' if env['APEX_LUSH'] else '0'}"
          f"  carousel={do_car}  video={do_vid}", flush=True)
    if do_car:
        run("build_today_pack.py", env)
    if do_vid:
        run("fast_render.py", env)
    print("\n[build_today] DONE. Outputs in generated_images/ (carousel folders + video/).", flush=True)

if __name__ == "__main__":
    main()
