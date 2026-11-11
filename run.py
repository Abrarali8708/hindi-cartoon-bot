"""Make one Hindi family-comedy cartoon and upload it.

  python run.py short                  # make + upload a Short (vertical, ~45 s)
  python run.py long                   # make + upload a long episode (~6-8 min)
  python run.py short --no-upload      # make only (saved in output/)
  python run.py short --sample --offline --no-upload   # test offline with the built-in sample story
"""
import argparse
import datetime as dt
import json
import random
import sys
from pathlib import Path

import yaml

from bot import aibg, animate, audio, script

ROOT = Path(__file__).resolve().parent
HIST = ROOT / "data" / "history.json"
GAP, SCENE_PAD, FPS = 0.22, 0.5, animate.FPS


def build_timeline(s, kind, out, offline, rng):
    voice, fx, t = [], [], 0.0
    intro = None
    if kind == "long":
        a = audio.speak(f"आज की कहानी: {s['title'].split('|')[0]}", "narrator", str(out / "intro.wav"), offline)
        voice.append((0.4, a))
        intro = {"end": 0.4 + len(a) / audio.SR + 0.6}
        fx.append((0.0, audio.sfx("whoosh")))
        t = intro["end"]
    scenes = []
    n = 0
    for si, sc in enumerate(s["scenes"]):
        start = t
        t += SCENE_PAD
        lines = []
        for ln in sc["lines"]:
            a = audio.speak(ln["text"], ln["who"], str(out / f"line_{n:03d}.wav"), offline)
            n += 1
            dur = len(a) / audio.SR
            item = dict(ln, start=t, end=t + dur, env=audio.envelope(a, FPS), react=rng.random() < 0.6)
            voice.append((t, a))
            if ln.get("sfx"):
                fx.append((t + dur if ln["sfx"] in ("punchline", "ding") else t, audio.sfx(ln["sfx"])))
            t += dur + GAP
            lines.append(item)
            print(f"    voice {n}: {ln['who']}")
        for i, ln in enumerate(lines):
            ln["end_hold"] = lines[i + 1]["start"] if i + 1 < len(lines) else t + 0.5
        t += 0.5
        scenes.append({"idx": si, "start": start, "end": t, "place": sc["place"], "cast": sc["cast"],
                       "lines": lines})
        if si + 1 < len(s["scenes"]):
            fx.append((t - 0.2, audio.sfx("whoosh")))
    # outro: moral
    a = audio.speak(f"सीख: {s['moral']}", "narrator", str(out / "moral.wav"), offline)
    outro_start = t
    voice.append((t + 0.3, a))
    fx.append((t, audio.sfx("ding")))
    t += 0.3 + len(a) / audio.SR + (2.2 if kind == "long" else 1.2)
    return dict(scenes=scenes, intro=intro, outro={"start": outro_start}, total=t), voice, fx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["short", "long"])
    ap.add_argument("--no-upload", action="store_true")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--sample", action="store_true", help="use the built-in sample story instead of Gemini")
    a = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    hist = json.loads(HIST.read_text()) if HIST.exists() else {"episodes": []}
    out = ROOT / "output" / a.kind
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random()

    if a.sample:
        s = script.validate(json.loads((ROOT / "assets" / f"sample_{a.kind}.json").read_text()), a.kind)
    else:
        s = script.write_episode(a.kind, cfg, [e["title"] for e in hist["episodes"]])
    print(f"→ {a.kind}: {s['title']}")
    (out / "script.json").write_text(json.dumps(s, ensure_ascii=False, indent=1))

    W, H = (1080, 1920) if a.kind == "short" else (1920, 1080)
    timeline, voice, fx = build_timeline(s, a.kind, out, a.offline, rng)
    if a.kind == "short" and timeline["total"] > cfg.get("short_max_seconds", 75):
        sys.exit(f"Short came out too long ({timeline['total']:.0f}s) - try again next run.")
    music = None
    tracks = sorted((ROOT / "music").glob("*.mp3"))
    if tracks:
        music = str(rng.choice(tracks))
    wav = str(out / "mix.wav")
    audio.save(wav, audio.mix(timeline["total"], voice, fx, music, cfg.get("music_volume", 0.07)))

    use_ai = bool(cfg.get("ai_backgrounds", True)) and not a.offline
    bgs = [aibg.background(sc["place"], (W, H), use_ai, out) for sc in timeline["scenes"]]
    if timeline["intro"]:
        timeline["intro"]["img"] = animate.title_card(s["title"].split("|")[0].strip(), W, H, sub=cfg["channel_name"])
    timeline["outro"]["img"] = animate.outro_card(s["moral"], W, H, cfg["channel_name"])
    mp4 = str(out / f"{a.kind}.mp4")
    print(f"  Rendering {timeline['total']:.0f}s of video...")
    animate.render(timeline, mp4, wav, W, H, bgs, hook=s["title"].split("|")[0] if a.kind == "short" else "")
    thumb = None
    if a.kind == "long":
        thumb = str(out / "thumb.jpg")
        animate.thumbnail(s, bgs[0], 1280, 720, thumb)
    print(f"  Video ready: {mp4} ({timeline['total'] / 60:.1f} min)")
    if a.no_upload:
        return

    from bot import upload
    title = s["title"].strip()
    if a.kind == "short" and "#shorts" not in title.lower():
        title = f"{title} #shorts"
    desc = (f"{s.get('description', '')}\n\nसीख: {s['moral']}\n\n"
            f"{cfg['channel_name']} - हर दिन नई मज़ेदार कहानी! चिंटू, पिंकी, मम्मी, पापा, दादी और गुप्ता जी के साथ।\n"
            "Subscribe करें और Bell icon दबाएं!\n\n"
            "Animated with AI-assisted tools: story written with AI help, AI voices. All characters are original.\n\n"
            "#hindicartoon #hindikahaniya #comedy #moralstories #cartoon" + (" #shorts" if a.kind == "short" else ""))
    vid = upload.upload(mp4, title[:100], desc, s["tags"] + ["hindi cartoon", "comedy cartoon", "hindi kahani"], cfg)
    print(f"  Uploaded: https://youtu.be/{vid}")
    if thumb:
        try:
            upload.set_thumbnail(vid, thumb)
            print("  Thumbnail set.")
        except Exception as e:
            print(f"  (thumbnail skipped - verify channel at youtube.com/verify: {e})")
    hist["episodes"].append({"kind": a.kind, "title": s["title"], "seed": s.get("seed"), "video_id": vid,
                             "at": dt.datetime.utcnow().isoformat(timespec="seconds")})
    HIST.write_text(json.dumps(hist, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
