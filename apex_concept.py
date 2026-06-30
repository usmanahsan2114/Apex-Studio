# -*- coding: utf-8 -*-
"""
apex_concept.py — FREE, offline daily concept + script generator for Apex Studio.

Builds a complete, valid `day_spec` (carousel + video + narration + captions) from a bank
of on-brand content PILLARS, picking a fresh pillar + phrasing variants each run and
injecting a random `seed` so the visual look co-randomizes. No API keys, no network.

This powers "Surprise me" / auto mode. The paste-from-GPT (APEX_SPEC) path is unchanged
and remains the way to author hand-tuned hero posts.

Voice rules baked in (see GPT_PROMPT_PRO.md): contrarian hook that inverts a belief,
one **amber** word per headline, the co-branded fix (Apex IT builds / Apex Marketings
turns into demand), CTA always contains "AUDIT", narration spelled for TTS
(Apex I-T, D-M AUDIT), digits-as-words, speed arc (slowest on the reframe).
"""
import os, random

BRAND_VO = "Apex I-T builds the system. Apex Marketings turns it into demand."
FB_TAGS = ["#smallbusinesspakistan", "#founders", "#digitalmarketing", "#karachi", "#lahore",
           "#islamabad", "#webdevelopment", "#b2bmarketing", "#leadgeneration", "#ecommerce",
           "#businessgrowth", "#seo", "#branding", "#startup"]

# Each pillar is a self-contained, on-brand concept. Multiple variants per slot => fresh runs.
PILLARS = [
 dict(key="speed_tax", lead="build", motif="speedometer", mood="tense", kicker="Speed Tax",
   topic="Your mobile site speed is quietly taxing revenue",
   hooks=[(["Your site is fast —", "**on your phone**", "only."],
           "On a real 4G phone it crawls — and that slower version is the one your buyers meet."),
          (["Fast on your phone.", "**Dead** on theirs."],
           "The version your customers load is nothing like the one you test.")],
   problem=(["3 seconds to load.", "**Half** your visitors gone."],
            "Past three seconds, mobile visitors bail — and you already paid for those clicks.",
            dict(head="What a slow page really costs", left="Bounced clicks + wasted ad spend", right="Sub-2s, leads kept")),
   peak=["Every slow second", "**bleeds** revenue."],
   reframe=(["Not a traffic problem.", "A **speed** problem."],
            "More ad budget just pours water into a leaking bucket — faster."),
   fix=(["Fix the page first.", "Then **scale** the spend."],
        ["Core Web Vitals", "Fast, owned build"], ["Ads that convert", "Pages that keep leads"]),
   ctas=[(["Speed is revenue", "you're **leaking**."], "Build the system. Turn it into demand.",
          'Curious how slow your site really is on a real phone? DM "AUDIT" and we\'ll time it, free.')],
   vo=["Your website is fast — on your phone. On a real one, it is quietly costing you.",
       "Most sites take over three seconds to load on mobile. That slower version is what your buyers actually get.",
       "Three seconds. That is all it takes to lose more than half of them.",
       "You do not have a traffic problem. You have a speed problem."],
   li_tags=["#CoreWebVitals", "#WebPerformance", "#B2BMarketing"]),

 dict(key="cost_of_cheap", lead="build", motif="roi_coins", mood="tense", kicker="Cost of Cheap",
   topic="A cheap website is the most expensive one you'll ever buy",
   hooks=[(["The cheap website is", "the **most expensive**", "one you'll ever buy."],
           "You didn't save money upfront. You financed the rebuild at a brutal rate."),
          (["Cheap now.", "**Expensive** forever."],
           "The lowest bid is a loan against your future revenue — with interest.")],
   problem=(["Rs 25,000 to build.", "**Rs 90,000** to fix."],
            "Add the rebuild, the bounced leads, and the ad spend burned on a broken page.",
            dict(head="What \"cheap\" actually costs", left="Rs 25k + the hidden invoice", right="Built right, once")),
   peak=["You financed", "the **rebuild**."],
   reframe=(["You never paid less.", "You just delayed", "the **invoice**."],
            "Cheap isn't a price. It's a loan against your future revenue."),
   fix=(["Build it right once.", "Then **scale** the demand."],
        ["Clean architecture", "Built to scale"], ["Profitable ad spend", "Page that converts"]),
   ctas=[(["Pay once for quality.", "Or **forever** for mistakes."], "Build the system. Turn it into demand.",
          'DM "AUDIT" and we\'ll price what your cheap build is quietly costing you, free.')],
   vo=["Here is the uncomfortable truth about a cheap website. It is the most expensive one you will ever buy.",
       "You save twenty-five thousand rupees upfront. Then you pay ninety thousand to fix it.",
       "The rebuild, the bounced leads, the ad spend burned on a page that could not convert.",
       "You never paid less. You just delayed the invoice six months."],
   li_tags=["#FounderLessons", "#WebDevelopment", "#B2BMarketing"]),

 dict(key="content_noise", lead="growth", motif="bar_grow", mood="driving", kicker="Signal System",
   topic="Posting daily without a content system is noise, not marketing",
   hooks=[(["Posting daily", "isn't a **strategy**.", "Rs 40k can vanish."],
           "A full calendar means nothing if every post points to a weak page and a vague offer."),
          (["A full feed.", "**Zero** demand."],
           "Busy is not the same as building demand. The calendar is only the visible edge.")],
   problem=(["A full calendar.", "Still **invisible**."],
            "The feed looks active, but buyers can't remember what you solve or why to trust you.",
            dict(head="What daily posting should move", left="Busy feed + low recall", right="Clear offer + qualified leads")),
   peak=["Rs 40k", "into the **void**."],
   reframe=(["The post", "is not", "the **asset**."],
            "The path behind the post — page, proof, follow-up — is the asset."),
   fix=(["Build the path.", "Then **amplify**."],
        ["Website Development", "Technical CRO"], ["Social Media Management", "Lead Generation"]),
   ctas=[(["Turn noise", "into **demand**."], "Build the system. Turn it into demand.",
          'DM "AUDIT" and we\'ll map where your content signal is leaking, free.')],
   vo=["Posting daily feels disciplined. But without a system behind it, it becomes expensive noise.",
       "Your feed can look full while buyers still forget what you solve, and where to go next.",
       "Even forty thousand rupees can disappear into posts nobody remembers by tomorrow.",
       "The post is not the asset. The path behind the post is the asset."],
   li_tags=["#B2BMarketing", "#LeadGeneration", "#SocialMediaStrategy"]),

 dict(key="leaky_funnel", lead="growth", motif="funnel", mood="tense", kicker="Leakproof Funnel",
   topic="More leads won't fix a funnel full of holes",
   hooks=[(["More leads won't", "fix a **leaking**", "funnel."],
           "You're pouring water into a bucket full of holes — then buying more water."),
          (["Buying leads.", "**Leaking** them."],
           "The problem isn't the top of the funnel. It's every hole below it.")],
   problem=(["Leads in.", "**Nothing** out."],
            "Slow pages, vague offers, and dead follow-up quietly drain every lead you pay for.",
            dict(head="Where the leads go", left="Paid clicks, leaking out", right="Captured + nurtured")),
   peak=["Most leads", "never **convert**."],
   reframe=(["You don't need", "more leads.", "You need to **keep** them."],
            "Fix the leaks first, and the leads you already pay for start converting."),
   fix=(["Seal the funnel.", "Then **fill** it."],
        ["Fast landing path", "Conversion tracking"], ["Offer that converts", "Follow-up system"]),
   ctas=[(["Stop **leaking**", "the leads you buy."], "Build the system. Turn it into demand.",
          'DM "AUDIT" and we\'ll find the holes in your funnel, free.')],
   vo=["You keep buying more leads to fix a funnel that leaks.",
       "Slow pages, vague offers, dead follow-up. Every one of them is a hole.",
       "Most of the leads you pay for never make it through.",
       "You do not need more leads. You need to stop losing the ones you have."],
   li_tags=["#LeadGeneration", "#CRO", "#B2BMarketing"]),

 dict(key="ads_are_rent", lead="growth", motif="growth_curve", mood="uplift", kicker="Owned Demand",
   topic="Ads are rent; an owned, ranking site is an asset you keep",
   hooks=[(["Ads are **rent**.", "Stop paying,", "traffic hits zero."],
           "The day you stop spending, the traffic you bought disappears. You only rented it."),
          (["You're renting", "your **growth**."],
           "Paused ads mean paused traffic. An owned, ranking asset keeps paying.")],
   problem=(["Pause the ads.", "Traffic goes **to zero**."],
            "Rented attention resets the moment the invoice stops. You own nothing.",
            dict(head="What your spend builds", left="Rented traffic", right="An owned asset")),
   peak=["Stop paying.", "Own **nothing**."],
   reframe=(["Ads rent attention.", "SEO + a site", "**own** it."],
            "An asset keeps paying you long after the invoice clears — and compounds."),
   fix=(["Build the asset.", "Then **scale** the rent."],
        ["Fast, owned site", "Technical SEO base"], ["Compounding SEO", "Ads that convert"]),
   ctas=[(["Stop renting", "your **growth**."], "Build the system. Turn it into demand.",
          'DM "AUDIT" and we\'ll show what you own vs what you rent, free.')],
   vo=["Ads rent attention. The day you stop paying, your traffic drops to zero.",
       "You poured budget into clicks on top of a site you do not really own.",
       "Rented traffic resets to zero. An owned asset keeps compounding.",
       "Build the asset first. Then scale the demand on top of it."],
   li_tags=["#SEO", "#DigitalMarketing", "#B2BMarketing"]),

 dict(key="out_waited", lead="growth", motif="line_trend", mood="uplift", kicker="Stamina System",
   topic="You're not getting outranked, you're getting out-waited",
   hooks=[(["You're not", "outranked.", "You're **out-waited**."],
           "Your competitors didn't beat you. They just didn't quit at month three."),
          (["SEO **compounds**.", "Your patience doesn't."],
           "Most founders quit right before the curve bends upward.")],
   problem=(["Month three.", "You **quit**."],
            "The results were one quarter away — and the competitor who waited took the rank.",
            dict(head="Why rankings slip away", left="Quit at month 3", right="Compounded past month 6")),
   peak=["They didn't quit.", "They **won**."],
   reframe=(["Rankings aren't", "won fast.", "They're **outlasted**."],
            "Consistency compounds. The brand that stays visible wins by default."),
   fix=(["Build to last.", "Then **outlast**."],
        ["SEO-ready build", "Fast, indexable site"], ["Compounding content", "Consistent SEO"]),
   ctas=[(["Win by", "**not quitting**."], "Build the system. Turn it into demand.",
          'DM "AUDIT" and we\'ll map your path to page one, free.')],
   vo=["You are not getting outranked. You are getting out-waited.",
       "Your competitors did not have a secret. They just did not quit at month three.",
       "Search rewards the brand that stays consistent and compounds.",
       "Rankings are not won fast. They are outlasted."],
   li_tags=["#SEO", "#ContentMarketing", "#FounderLessons"]),
]

SPEEDS = [0.97, 1.0, 0.95, 0.95, 1.0, 1.0]
MEM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art_memory.json")

def _recent_pillars():
    try:
        import json
        with open(MEM, encoding="utf-8") as f:
            return (json.load(f) or {}).get("recent_pillars", [])
    except Exception:
        return []

def _remember_pillar(key):
    try:
        import json
        data = {}
        try:
            with open(MEM, encoding="utf-8") as f: data = json.load(f) or {}
        except Exception:
            data = {}
        rec = data.get("recent_pillars", [])
        if rec and rec[-1] == key: return
        rec.append(key); data["recent_pillars"] = rec[-4:]
        with open(MEM, "w", encoding="utf-8") as f: json.dump(data, f)
    except Exception:
        pass

def _pick_pillar(rng):
    recent = set(_recent_pillars())
    pool = [p for p in PILLARS if p["key"] not in recent] or PILLARS
    return rng.choice(pool)

def _short(headline):
    """Trim a carousel headline to <=2 lines for a punchier video scene."""
    return headline if len(headline) <= 2 else [headline[0], headline[-1]]

def generate(seed=None, topic=None, date=None):
    """Return a fresh, valid, on-brand day_spec dict (random pillar + variants + seed)."""
    if seed is None:
        seed = random.getrandbits(31)
    rng = random.Random(seed)
    p = _pick_pillar(rng)
    _remember_pillar(p["key"])
    hook_h, hook_sub = rng.choice(p["hooks"])
    cta_h, cta_sub, cta_line = rng.choice(p["ctas"])
    prob_h, prob_sub, meter = p["problem"]
    ref_h, ref_sub = p["reframe"]
    fix_h, fix_build, fix_growth = p["fix"]
    kicker = p["kicker"]
    date = date or ""
    suffix = "%04x" % (seed & 0xFFFF)

    carousel = {
        "kicker": kicker,
        "slides": [
            {"motif": "", "headline": hook_h, "sub": hook_sub},
            {"tag": "The problem", "headline": prob_h, "sub": prob_sub, "meter": meter},
            {"headline": ref_h, "sub": ref_sub},
            {"tag": "The fix", "headline": fix_h, "build_chips": fix_build, "growth_chips": fix_growth},
            {"headline": cta_h, "sub": cta_sub, "cta": cta_line},
        ],
        "linkedin": {"caption": _li_caption(p, hook_sub, ref_sub, cta_line), "hashtags": p["li_tags"][:3]},
        "fb": {"caption": _fb_caption(p, cta_line), "hashtags": _fb_tags(rng, p)},
    }
    vo = p["vo"] + [BRAND_VO, _audit_spoken(cta_line)]
    narration = [{"text": vo[i], "speed": SPEEDS[i]} for i in range(6)]
    peak_h = p.get("peak", ref_h)  # distinct beat-3 punch (never duplicate the problem headline)
    scenes = [
        {"headline": hook_h, "big": True, "punch_at": 0.32},
        {"tag": "The problem", "headline": prob_h, "sub": prob_sub.split(".")[0] + "."},
        {"headline": peak_h, "big": True, "punch_at": 0.5},
        {"headline": ref_h, "big": True, "punch_at": 0.5},
        {"tag": "The fix", "headline": fix_h, "build_chips": fix_build, "growth_chips": fix_growth},
        {"headline": cta_h, "cta": cta_line},
    ]
    video = {
        "kicker": kicker, "music_mood": p["mood"], "motif_name": p["motif"], "motif_scenes": [0, 2],
        "narration": narration, "scenes": scenes, "caption": _video_caption(p, cta_line),
    }
    spec = {"id": p["key"] + "_" + suffix, "date": date, "topic": p["topic"],
            "seed": seed, "look": "auto", "carousel": carousel, "video": video}
    try:
        import apex_spec
        ok, errs = apex_spec.validate(spec)
        if not ok:
            raise ValueError("generated spec invalid: %s" % errs)
    except ImportError:
        pass
    return spec

# ---- caption builders (plain text; hashtags appended by callers/_caption) ----
def _flat(lines):
    return " ".join(x.replace("**", "") for x in lines)

def _li_caption(p, hook_sub, ref_sub, cta_line):
    return (f"{_flat(p['hooks'][0][0])}\n\n{hook_sub}\n\n{ref_sub}\n\n"
            f"Apex IT builds the system; Apex Marketings turns it into demand.\n\n"
            f"{cta_line.replace(chr(34)+'AUDIT'+chr(34), '“AUDIT”')}\n\n"
            f"What would change for you if this were fixed?")

def _fb_caption(p, cta_line):
    return (f"Save this.\n\n{p['topic']}.\n\n"
            f"Apex IT fixes the build; Apex Marketings turns it into leads.\n\n{cta_line}")

def _video_caption(p, cta_line):
    return (f"Sound on. \U0001f50a {p['topic']}.\n\n"
            f"Apex IT builds the system; Apex Marketings turns it into demand. {cta_line}\n\n"
            f"What's the weakest link in your funnel right now?\n\n"
            + " ".join(p["li_tags"] + ["#smallbusinesspakistan", "#founders", "#digitalmarketing"]))

def _audit_spoken(cta_line):
    return "D-M AUDIT, and we'll show you exactly where to start, free."

def _fb_tags(rng, p):
    pool = list(FB_TAGS)
    rng.shuffle(pool)
    return pool[:10]

if __name__ == "__main__":
    import json
    s = generate(seed=12345)
    print(json.dumps(s, ensure_ascii=False, indent=2)[:1500])
