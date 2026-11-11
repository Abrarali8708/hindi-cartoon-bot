"""Cartoon renderer: puts the family on a background, makes them talk (lip-sync), blink, bounce and react,
adds Hindi captions, zooms, shakes on punchlines, and writes an MP4."""
import json
import math
import random
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
CHAR_DIR = ROOT / "assets" / "characters"
FPS = 24
NAMES_HI = {"chintu": "चिंटू", "pinky": "पिंकी", "mummy": "मम्मी", "papa": "पापा", "dadi": "दादी",
            "guptaji": "गुप्ता जी", "narrator": ""}
NAME_COL = {"chintu": "#e63946", "pinky": "#ff4fa0", "mummy": "#1f8a7e", "papa": "#1d7fb0", "dadi": "#9b2226",
            "guptaji": "#5f0f40", "narrator": "#444444"}
ARMS = {"angry": "hips", "surprised": "up", "laugh": "up"}
BROWS = {"laugh": "happy"}
REST_MOUTH = {"neutral": "smile", "happy": "smile", "laugh": "big", "angry": "frown", "sad": "frown",
              "surprised": "o"}
REACT = {"laugh": "happy", "surprised": "surprised", "angry": "sad", "sad": "sad", "happy": "happy"}

FONT_CANDIDATES = [ROOT / "assets" / "fonts" / "Hindi-Bold.ttf",
                   Path("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"),
                   Path("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"),
                   Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf")]


def font(size):
    for p in FONT_CANDIDATES:
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size, layout_engine=ImageFont.Layout.RAQM)
            except Exception:
                return ImageFont.truetype(str(p), size)
    raise RuntimeError("No Hindi font found - install fonts-noto-core")


def clean(text):
    """Remove emoji / symbols the Hindi font can't draw."""
    return "".join(ch for ch in text if ord(ch) < 0x2000 or 0x0900 <= ord(ch) <= 0x097F or ch in "।॥").strip()


def ease(p):
    p = min(max(p, 0.0), 1.0)
    return 1 - (1 - p) ** 3


# ---------------------------------------------------------------- characters
class Sprites:
    def __init__(self, scale_px):
        self.meta = json.loads((CHAR_DIR / "cast.json").read_text())
        self.scale_px = scale_px          # canvas height in px for a scale-1.0 character
        self.layers, self.cache = {}, {}

    def _layer(self, who, name):
        k = (who, name)
        if k not in self.layers:
            im = Image.open(CHAR_DIR / who / f"{name}.png").convert("RGBA")
            s = self.scale_px * self.meta[who]["scale"] / im.height
            self.layers[k] = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        return self.layers[k]

    def get(self, who, arms, eyes, brows, mouth):
        k = (who, arms, eyes, brows, mouth)
        if k not in self.cache:
            im = self._layer(who, "base").copy()
            for n in (f"arms_{arms}", f"eyes_{eyes}", f"brows_{brows}", f"mouth_{mouth}", "top"):
                im.alpha_composite(self._layer(who, n))
            self.cache[k] = im
        return self.cache[k]


# ---------------------------------------------------------------- captions / cards
def caption_img(who, text, width, size):
    text = clean(text)
    f, fn = font(size), font(int(size * 0.72))
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) > width - 2 * size:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    lh = int(size * 1.45)
    name = NAMES_HI.get(who, "")
    top = int(size * 1.15) if name else 0
    h = top + lh * len(lines) + int(size * 0.6)
    im = Image.new("RGBA", (width, h + 8), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((4, top // 2 + 4, width - 4, h + 4), radius=size // 2, fill=(255, 255, 255, 236),
                         outline=NAME_COL.get(who, "#333"), width=6)
    if name:
        nw = int(dr.textlength(name, font=fn)) + size
        dr.rounded_rectangle((size // 2, 0, size // 2 + nw, top + 6), radius=size // 3, fill=NAME_COL[who])
        dr.text((size // 2 + size // 2, top // 2 + 3), name, font=fn, fill="white", anchor="lm")
    for i, ln in enumerate(lines):
        dr.text((width // 2, top + int(size * 0.35) + lh * i + lh // 2), ln, font=f, fill="#1b1b1b", anchor="mm")
    return im


def title_card(text, W, H, sub=""):
    text = clean(text)
    im = Image.new("RGB", (W, H), "#ffcf3f")
    dr = ImageDraw.Draw(im)
    for i in range(0, W + H, 90):   # sunburst stripes
        dr.polygon([(W // 2, H // 2), (i, 0), (i + 45, 0)], fill="#ffbf1f")
        dr.polygon([(W // 2, H // 2), (i - H, H), (i - H + 45, H)], fill="#ffbf1f")
    size = int(min(W, H) * 0.115)
    f = font(size)
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if dr.textlength(t, font=f) > W * 0.86:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    y0 = H // 2 - len(lines) * size * 0.65
    for i, ln in enumerate(lines):
        dr.text((W // 2, y0 + i * size * 1.3), ln, font=f, fill="#ffffff", anchor="mm", stroke_width=size // 9,
                stroke_fill="#2b1d14")
    if sub:
        dr.text((W // 2, y0 + len(lines) * size * 1.3 + size * 0.4), sub, font=font(int(size * 0.55)),
                fill="#2b1d14", anchor="mm")
    return im


# ---------------------------------------------------------------- layout
def slots(n, W, H, tall):
    xs = {1: [0.5], 2: [0.3, 0.7], 3: [0.18, 0.5, 0.82]}[n]
    if tall:
        xs = {1: [0.5], 2: [0.27, 0.73], 3: [0.17, 0.5, 0.83]}[n]
    return [x * W for x in xs]


def render(timeline, out_mp4, wav, W, H, backgrounds, hook=""):
    """timeline: dict(scenes=[{start,end,place,cast,lines:[{who,emotion,text,start,end,env,sfx}]}], intro, outro, total)"""
    tall = H > W
    char_h = H * (0.46 if tall else 0.84)
    sprites = Sprites(char_h)
    feet = H * (0.80 if tall else 1.0)
    cap_w = int(W * (0.92 if tall else 0.8))
    cap_size = int(H * (0.031 if tall else 0.045))
    rng = random.Random(7)
    blink_next = {}
    caps = {}
    hook_img = None
    hook = clean(hook)
    if hook:
        f = font(int(W * 0.07))
        hook_img = Image.new("RGBA", (W, int(H * 0.2)), (0, 0, 0, 0))
        hd = ImageDraw.Draw(hook_img)
        words, lines, cur = hook.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if hd.textlength(t, font=f) > W * 0.9:
                lines.append(cur)
                cur = w
            else:
                cur = t
        lines.append(cur)
        for i, ln in enumerate(lines[:2]):
            hd.text((W // 2, int(H * 0.075) + i * int(W * 0.085)), ln, font=f, fill="#ffde59", anchor="mm",
                    stroke_width=8, stroke_fill="#1b1b1b")

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
           "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
           "-ar", "44100", "-t", f"{timeline['total']:.2f}", "-movflags", "+faststart", out_mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n_frames = int(timeline["total"] * FPS)
    intro, outro = timeline.get("intro"), timeline.get("outro")
    last_key, last_bytes = None, None

    for fi in range(n_frames):
        t = fi / FPS
        if intro and t < intro["end"]:
            frame = _zoomed(intro["img"], 1 + 0.04 * t / intro["end"], W / 2, H / 2)
            proc.stdin.write(frame.tobytes())
            continue
        if outro and t >= outro["start"]:
            frame = _zoomed(outro["img"], 1 + 0.03 * (t - outro["start"]) / max(0.1, timeline["total"] - outro["start"]),
                            W / 2, H / 2)
            proc.stdin.write(frame.tobytes())
            continue
        sc = next((s for s in timeline["scenes"] if s["start"] <= t < s["end"]), timeline["scenes"][-1])
        bg = backgrounds[sc["idx"]]
        line = next((ln for ln in sc["lines"] if ln["start"] <= t < ln["end_hold"]), None)
        speaking = line if line and t < line["end"] else None
        xs = slots(len(sc["cast"]), W, H, tall)
        frame = bg.copy().convert("RGBA")
        key_parts = [sc["idx"]]
        for i, who in enumerate(sc["cast"]):
            # entry slide
            enter = ease((t - sc["start"]) / 0.45)
            side = -1 if xs[i] < W / 2 else 1
            x = xs[i] + side * (1 - enter) * W * 0.6
            # emotion
            emo = "neutral"
            if line:
                if line["who"] == who:
                    emo = line["emotion"]
                elif t - line["start"] > 0.3 and line["react"]:
                    emo = REACT.get(line["emotion"], "neutral")
            is_spk = speaking is not None and speaking["who"] == who
            # mouth
            mouth = REST_MOUTH[emo]
            if is_spk:
                k = int((t - speaking["start"]) * FPS)
                lv = speaking["env"][k] if k < len(speaking["env"]) else 0
                mouth = (REST_MOUTH[emo] if lv < 0.18 else
                         ("o" if emo == "surprised" else "small") if lv < 0.55 else "big")
            # eyes (blink)
            nb = blink_next.setdefault(who, rng.uniform(1, 4))
            eyes = "happy" if emo in ("laugh",) else "open"
            if nb <= t < nb + 0.13:
                eyes = "closed"
            elif t >= nb + 0.13:
                blink_next[who] = t + rng.uniform(2.2, 5.0)
            arms = ARMS.get(emo, "down") if (is_spk or emo in ("surprised",)) else ("hips" if emo == "angry" else "down")
            spr = sprites.get(who, arms, eyes, BROWS.get(emo, emo if emo != "laugh" else "happy"), mouth)
            # bounce / breathing
            bob = math.sin(2 * math.pi * 0.5 * t + i) * 3
            if is_spk:
                bob -= abs(math.sin(2 * math.pi * 2.4 * t)) * H * 0.008
            px, py = int(x - spr.width / 2), int(feet - spr.height + bob)
            frame.alpha_composite(spr, (max(-spr.width, min(W, px)), py)) if -spr.width < px < W else None
            key_parts.append((who, round(x), round(bob), arms, eyes, emo, mouth))
        # caption
        if line:
            ck = id(line)
            if ck not in caps:
                caps[ck] = caption_img(line["who"], line["text"], cap_w, cap_size)
            ci = caps[ck]
            cy = int(H * 0.11) if tall else int(H - ci.height - H * 0.035)
            frame.alpha_composite(ci, ((W - ci.width) // 2, cy + (int(H * 0.08) if tall and hook_img is not None
                                                                      and t < 2.5 else 0)))
            key_parts.append(ck)
        if hook_img is not None and t < 2.5:
            frame.alpha_composite(hook_img, (0, 0))
            key_parts.append("hook")
        # camera: zoom towards speaker, shake on punchline, fade between scenes
        z, cx = 1.0, W / 2
        if speaking:
            si = sc["cast"].index(speaking["who"]) if speaking["who"] in sc["cast"] else None
            if si is not None:
                p = ease((t - speaking["start"]) / max(0.6, speaking["end"] - speaking["start"]))
                z = 1 + 0.06 * p
                cx = W / 2 + (xs[si] - W / 2) * 0.35 * p
        shake = 0
        if line and line.get("sfx") == "punchline" and line["end"] <= t < line["end"] + 0.35:
            shake = int(10 * math.sin(t * 90))
        key = (tuple(key_parts), round(z, 3), round(cx), shake)
        if key == last_key:
            proc.stdin.write(last_bytes)
            continue
        out = _zoomed(frame.convert("RGB"), z, cx + shake, H / 2)
        fade = min(1, (t - sc["start"]) / 0.25, (sc["end"] - t) / 0.25)
        if fade < 1:
            out = Image.blend(Image.new("RGB", (W, H), "white"), out, max(0.0, fade))
        last_key, last_bytes = key, out.tobytes()
        proc.stdin.write(last_bytes)
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed")


def _zoomed(img, z, cx, cy):
    if z <= 1.001:
        return img if img.mode == "RGB" else img.convert("RGB")
    W, H = img.size
    w, h = W / z, H / z
    x0 = min(max(cx - w / 2, 0), W - w)
    y0 = min(max(cy - h / 2, 0), H - h)
    return img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h))


def outro_card(moral, W, H, channel):
    im = title_card("सीख: " + moral, W, H, sub=f"{channel} को Subscribe करें!")
    sprites = Sprites(H * (0.3 if H > W else 0.42))
    cast = ["chintu", "mummy", "papa", "dadi", "pinky"] if W > H else ["chintu", "dadi", "pinky"]
    for i, who in enumerate(cast):
        spr = sprites.get(who, "up" if i % 2 == 0 else "down", "happy", "happy", "smile")
        x = int(W * (i + 0.5) / len(cast) - spr.width / 2)
        im.paste(spr, (x, int(H - spr.height * (0.62 if H > W else 0.55))), spr)
    return im


def thumbnail(script, place_bg, W, H, out_png):
    im = place_bg.copy().resize((W, H)).filter(ImageFilter.GaussianBlur(2)).convert("RGBA")
    sprites = Sprites(H * 1.15)
    first = script["scenes"][0]["cast"][:2]
    for i, who in enumerate(first):
        spr = sprites.get(who, "up" if i == 0 else "hips", "open", "surprised" if i == 0 else "angry",
                          "big" if i == 0 else "o")
        x = int(W * (0.2 if i == 0 else 0.8) - spr.width / 2)
        im.alpha_composite(spr, (x, int(H * 0.08)))
    dr = ImageDraw.Draw(im)
    size = int(H * 0.15)
    f = font(size)
    text = clean(script.get("thumb_text") or script["title"])
    dr.text((W // 2, int(H * 0.82)), text, font=f, fill="#ffde59", anchor="mm", stroke_width=size // 8,
            stroke_fill="#1b1b1b")
    im.convert("RGB").save(out_png, quality=92)
