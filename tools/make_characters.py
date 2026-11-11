"""Draw the cartoon family as layered sprites (run once; PNGs are committed to assets/).

Every character is drawn on the same 600x1000 canvas so layers line up:
  base.png                         body, head, hair
  arms_down / arms_up / arms_hips  arm poses
  eyes_open / eyes_closed / eyes_happy
  brows_<emotion>                  neutral happy angry sad surprised
  mouth_<shape>                    smile flat frown small big o
  top.png                          glasses / moustache / bindi (drawn over the face)
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "assets/characters")
W, H = 600, 1000
INK = "#2b1d14"
SW = 7  # outline width

CAST = {
    "chintu": dict(kind="kid", skin="#c98b5e", hair="kid_spiky", shirt="#e63946", shirt2="#ffd166",
                   bottom="#1d4e89", shoes="#f1faee", scale=0.80, glasses=None, moustache=None),
    "pinky": dict(kind="girl", skin="#d39a6a", hair="ponytails", shirt="#ff6fae", shirt2="#ffe3f1",
                  bottom="#ff6fae", shoes="#e63946", scale=0.74, glasses=None, moustache=None),
    "mummy": dict(kind="woman", skin="#c68a5a", hair="bun", shirt="#2a9d8f", shirt2="#f4a261",
                  bottom="#2a9d8f", shoes="#8d5524", scale=1.0, glasses=None, moustache=None, bindi=True),
    "papa": dict(kind="man", skin="#b97a4f", hair="side", shirt="#8ecae6", shirt2="#219ebc",
                 bottom="#3d405b", shoes="#3b2a20", scale=1.03, glasses="rect", moustache="thin"),
    "dadi": dict(kind="woman", skin="#c99470", hair="grey_bun", shirt="#fff3d6", shirt2="#9b2226",
                 bottom="#fff3d6", shoes="#6c584c", scale=0.93, glasses="round", moustache=None, bindi=True,
                 wrinkles=True),
    "guptaji": dict(kind="man", skin="#a86b43", hair="bald", shirt="#fdfdfd", shirt2="#d9d9d9",
                    bottom="#5f0f40", shoes="#3b2a20", scale=1.0, glasses=None, moustache="big", vest=True),
}

HX, HY = 300, 255           # head centre
EYE_Y, EYE_DX = 268, 52
MOUTH_Y = 338


def svg(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<g stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round" stroke-linecap="round">{body}</g></svg>')


def head_r(c):
    return 150 if c["kind"] in ("kid", "girl") else 138


# ---------------------------------------------------------------- base
def base(c):
    r = head_r(c)
    s, p = [], []
    adult = c["kind"] in ("man", "woman")
    top = 400 if not adult else 395
    # back hair
    if c["hair"] == "ponytails":
        for sx in (-1, 1):
            x = HX + sx * (r + 25)
            s.append(f'<path d="M{HX + sx * (r - 30)} {HY - 60} Q{x + sx * 50} {HY - 20} {x + sx * 20} {HY + 120} '
                     f'Q{x - sx * 10} {HY + 40} {HX + sx * (r - 20)} {HY - 10} Z" fill="#1b1b1b"/>')
            s.append(f'<circle cx="{HX + sx * (r - 10)}" cy="{HY - 70}" r="20" fill="{c["shirt"]}"/>')
    if c["hair"] in ("bun", "grey_bun"):
        col = "#1b1b1b" if c["hair"] == "bun" else "#c9c9c9"
        s.append(f'<circle cx="{HX}" cy="{HY - r - 20}" r="52" fill="{col}"/>')
        s.append(f'<path d="M{HX - r + 5} {HY + 10} Q{HX - r - 15} {HY + 140} {HX - r + 40} {HY + 150} L{HX + r - 40} '
                 f'{HY + 150} Q{HX + r + 15} {HY + 140} {HX + r - 5} {HY + 10} Z" fill="{col}"/>')
    # legs + shoes
    leg_top = 760 if adult else 735
    for sx in (-1, 1):
        lx = HX + sx * 48
        if c["kind"] == "woman":
            continue
        s.append(f'<rect x="{lx - 26}" y="{leg_top}" width="52" height="{960 - leg_top - 30}" rx="20" fill="{c["skin"] if c["kind"] in ("kid", "girl") else c["bottom"]}"/>')
        s.append(f'<ellipse cx="{lx + sx * 14}" cy="955" rx="52" ry="26" fill="{c["shoes"]}"/>')
    # torso / clothes
    if c["kind"] == "kid":
        s.append(f'<path d="M{HX - 120} {top + 20} Q{HX} {top - 20} {HX + 120} {top + 20} L{HX + 128} {leg_top + 10} '
                 f'L{HX - 128} {leg_top + 10} Z" fill="{c["shirt"]}"/>')
        s.append(f'<path d="M{HX - 128} {leg_top - 70} L{HX + 128} {leg_top - 70} L{HX + 132} {leg_top + 70} '
                 f'L{HX + 8} {leg_top + 70} L{HX} {leg_top + 20} L{HX - 8} {leg_top + 70} L{HX - 132} {leg_top + 70} Z" '
                 f'fill="{c["bottom"]}"/>')
        s.append(_star(HX, top + 150, 42, c["shirt2"]))
    elif c["kind"] == "girl":
        s.append(f'<path d="M{HX - 95} {top + 15} Q{HX} {top - 20} {HX + 95} {top + 15} L{HX + 175} {leg_top + 40} '
                 f'Q{HX} {leg_top + 80} {HX - 175} {leg_top + 40} Z" fill="{c["shirt"]}"/>')
        for i in range(5):
            s.append(f'<circle cx="{HX - 110 + i * 55}" cy="{leg_top + 10}" r="9" fill="{c["shirt2"]}" stroke-width="3"/>')
        s.append(f'<path d="M{HX - 95} {top + 120} Q{HX} {top + 150} {HX + 95} {top + 120}" fill="none" '
                 f'stroke="{c["shirt2"]}" stroke-width="16"/>')
    elif c["kind"] == "woman":   # saree
        s.append(f'<path d="M{HX - 130} {top + 25} Q{HX} {top - 25} {HX + 130} {top + 25} L{HX + 150} 940 '
                 f'Q{HX} 965 {HX - 150} 940 Z" fill="{c["shirt"]}"/>')
        s.append(f'<path d="M{HX - 150} 905 Q{HX} 930 {HX + 150} 905 L{HX + 150} 940 Q{HX} 965 {HX - 150} 940 Z" '
                 f'fill="{c["shirt2"]}"/>')
        s.append(f'<path d="M{HX + 120} {top + 20} L{HX - 70} {top + 330} L{HX - 20} {top + 360} L{HX + 140} {top + 90} Z" '
                 f'fill="{c["shirt2"]}"/>')   # pallu
        for sx in (-1, 1):
            s.append(f'<ellipse cx="{HX + sx * 55}" cy="955" rx="46" ry="22" fill="{c["shoes"]}"/>')
    else:  # man
        belly = 30 if c.get("vest") else 15
        s.append(f'<path d="M{HX - 135} {top + 25} Q{HX} {top - 25} {HX + 135} {top + 25} Q{HX + 150 + belly} '
                 f'{(top + leg_top) / 2} {HX + 135} {leg_top + 20} L{HX - 135} {leg_top + 20} Q{HX - 150 - belly} '
                 f'{(top + leg_top) / 2} {HX - 135} {top + 25} Z" fill="{c["shirt"]}"/>')
        if c.get("vest"):
            s.append(f'<path d="M{HX - 60} {top + 2} Q{HX} {top + 90} {HX + 60} {top + 2}" fill="{c["skin"]}"/>')
        else:
            s.append(f'<path d="M{HX - 45} {top - 2} L{HX} {top + 60} L{HX + 45} {top - 2}" fill="#ffffff"/>')
            s.append(f'<line x1="{HX}" y1="{top + 60}" x2="{HX}" y2="{leg_top + 10}" stroke-width="4"/>')
            for i in range(4):
                s.append(f'<circle cx="{HX + 14}" cy="{top + 100 + i * 70}" r="7" fill="{c["shirt2"]}" stroke-width="3"/>')
        s.append(f'<rect x="{HX - 140}" y="{leg_top}" width="280" height="34" rx="10" fill="#3b2a20"/>')
    # neck + head + ears
    s.append(f'<rect x="{HX - 32}" y="{HY + r - 30}" width="64" height="60" fill="{c["skin"]}"/>')
    for sx in (-1, 1):
        s.append(f'<ellipse cx="{HX + sx * (r - 4)}" cy="{HY + 15}" rx="28" ry="36" fill="{c["skin"]}"/>')
        if c["kind"] == "woman":
            s.append(f'<circle cx="{HX + sx * (r - 4)}" cy="{HY + 58}" r="11" fill="#ffd166" stroke-width="4"/>')
    s.append(f'<ellipse cx="{HX}" cy="{HY}" rx="{r}" ry="{r * 0.97:.0f}" fill="{c["skin"]}"/>')
    # cheeks
    for sx in (-1, 1):
        s.append(f'<ellipse cx="{HX + sx * 82}" cy="{HY + 55}" rx="24" ry="14" fill="#ff8fa3" stroke="none" opacity="0.55"/>')
    if c.get("wrinkles"):
        for sx in (-1, 1):
            s.append(f'<path d="M{HX + sx * 95} {EYE_Y - 8} l{sx * 18} -6 M{HX + sx * 97} {EYE_Y + 6} l{sx * 18} 2" '
                     f'stroke-width="3" fill="none"/>')
        s.append(f'<path d="M{HX - 45} {HY - 85} q45 -10 90 0" stroke-width="3" fill="none"/>')
    # front hair
    hair = {"kid_spiky": _hair_spiky, "ponytails": _hair_fringe, "bun": _hair_parted, "grey_bun": _hair_parted,
            "side": _hair_side, "bald": _hair_bald}[c["hair"]]
    s.append(hair(c, r))
    return "".join(s)


def _star(cx, cy, r, fill):
    import math
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append(f"{cx + rr * math.cos(a):.1f},{cy + rr * math.sin(a):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke-width="4"/>'


def _hair_spiky(c, r):
    return (f'<path d="M{HX - r + 5} {HY - 10} Q{HX - r} {HY - r - 10} {HX - 40} {HY - r - 15} L{HX - 20} {HY - r - 55} '
            f'L{HX + 10} {HY - r - 10} L{HX + 45} {HY - r - 50} L{HX + 60} {HY - r - 5} Q{HX + r} {HY - r + 10} '
            f'{HX + r - 5} {HY - 10} Q{HX + 70} {HY - 95} {HX + 10} {HY - 80} Q{HX - 60} {HY - 105} {HX - r + 5} {HY - 10} Z" '
            f'fill="#1b1b1b"/>')


def _hair_fringe(c, r):
    return (f'<path d="M{HX - r + 2} {HY + 10} Q{HX - r - 5} {HY - r - 10} {HX} {HY - r - 8} Q{HX + r + 5} {HY - r - 10} '
            f'{HX + r - 2} {HY + 10} Q{HX + r - 30} {HY - 60} {HX + 80} {HY - 70} L{HX + 60} {HY - 95} L{HX + 30} '
            f'{HY - 70} L{HX} {HY - 95} L{HX - 30} {HY - 70} L{HX - 60} {HY - 95} L{HX - 80} {HY - 70} '
            f'Q{HX - r + 30} {HY - 60} {HX - r + 2} {HY + 10} Z" fill="#1b1b1b"/>')


def _hair_parted(c, r):
    col = "#1b1b1b" if c["hair"] == "bun" else "#c9c9c9"
    return (f'<path d="M{HX - r + 2} {HY + 25} Q{HX - r - 5} {HY - r - 5} {HX} {HY - r - 6} Q{HX + r + 5} {HY - r - 5} '
            f'{HX + r - 2} {HY + 25} Q{HX + r - 25} {HY - 70} {HX + 5} {HY - 95} L{HX} {HY - 80} L{HX - 5} {HY - 95} '
            f'Q{HX - r + 25} {HY - 70} {HX - r + 2} {HY + 25} Z" fill="{col}"/>')


def _hair_side(c, r):
    return (f'<path d="M{HX - r + 2} {HY + 5} Q{HX - r - 5} {HY - r - 5} {HX} {HY - r - 8} Q{HX + r + 8} {HY - r} '
            f'{HX + r - 2} {HY + 5} Q{HX + r - 40} {HY - 80} {HX - 20} {HY - 90} Q{HX - r + 40} {HY - 70} '
            f'{HX - r + 2} {HY + 5} Z" fill="#1b1b1b"/>')


def _hair_bald(c, r):
    return "".join(f'<path d="M{HX + sx * (r - 2)} {HY + 30} Q{HX + sx * (r + 8)} {HY - 40} {HX + sx * (r - 45)} '
                   f'{HY - 80} Q{HX + sx * (r - 30)} {HY - 20} {HX + sx * (r - 2)} {HY + 30} Z" fill="#3a3a3a"/>'
                   for sx in (-1, 1)) + \
        f'<path d="M{HX - 40} {HY - 105} q15 -12 30 -4" stroke="#ffffff" stroke-width="6" fill="none" opacity="0.6"/>'


# ---------------------------------------------------------------- arms
def arms(c, pose):
    adult = c["kind"] in ("man", "woman")
    sh_y = 450 if adult else 455
    sw = 132 if adult else 118
    sleeve = c["shirt"] if c["kind"] != "woman" else c["shirt"]
    out = []
    for sx in (-1, 1):
        x0 = HX + sx * sw
        if pose == "down":
            pts = f"M{x0} {sh_y} Q{x0 + sx * 40} {sh_y + 140} {x0 + sx * 18} {sh_y + 250}"
            hand = (x0 + sx * 18, sh_y + 262)
        elif pose == "up":
            pts = f"M{x0} {sh_y} Q{x0 + sx * 90} {sh_y - 40} {x0 + sx * 95} {sh_y - 170}"
            hand = (x0 + sx * 95, sh_y - 182)
        else:  # hips
            pts = f"M{x0} {sh_y} Q{x0 + sx * 95} {sh_y + 100} {x0 - sx * 2} {sh_y + 190}"
            hand = (x0 - sx * 2, sh_y + 190)
        out.append(f'<path d="{pts}" fill="none" stroke="{INK}" stroke-width="44"/>')
        out.append(f'<path d="{pts}" fill="none" stroke="{c["skin"]}" stroke-width="30"/>')
        # sleeve
        out.append(f'<circle cx="{x0}" cy="{sh_y + 5}" r="32" fill="{sleeve}"/>')
        out.append(f'<circle cx="{hand[0]}" cy="{hand[1]}" r="26" fill="{c["skin"]}"/>')
    return "".join(out)


# ---------------------------------------------------------------- face
def eyes(c, state):
    out = []
    for sx in (-1, 1):
        x = HX + sx * EYE_DX
        if state == "open":
            out.append(f'<ellipse cx="{x}" cy="{EYE_Y}" rx="25" ry="31" fill="#ffffff" stroke-width="5"/>')
            out.append(f'<circle cx="{x + 3}" cy="{EYE_Y + 4}" r="15" fill="#2b1d14" stroke="none"/>')
            out.append(f'<circle cx="{x + 9}" cy="{EYE_Y - 4}" r="5.5" fill="#ffffff" stroke="none"/>')
        elif state == "closed":
            out.append(f'<path d="M{x - 24} {EYE_Y + 4} Q{x} {EYE_Y + 18} {x + 24} {EYE_Y + 4}" fill="none" stroke-width="6"/>')
        else:  # happy ^ ^
            out.append(f'<path d="M{x - 24} {EYE_Y + 10} Q{x} {EYE_Y - 18} {x + 24} {EYE_Y + 10}" fill="none" stroke-width="6"/>')
    return "".join(out)


def brows(c, emo):
    col = "#c9c9c9" if c["hair"] == "grey_bun" else "#1b1b1b"
    y = EYE_Y - 48
    out = []
    for sx in (-1, 1):
        x = HX + sx * EYE_DX
        inner, outer = x - sx * 24, x + sx * 24
        if emo == "angry":
            d = f"M{outer} {y - 8} L{inner} {y + 10}"
        elif emo == "sad":
            d = f"M{outer} {y + 8} L{inner} {y - 10}"
        elif emo == "surprised":
            d = f"M{outer} {y - 6} Q{x} {y - 26} {inner} {y - 6}"
        elif emo == "happy":
            d = f"M{outer} {y} Q{x} {y - 16} {inner} {y}"
        else:
            d = f"M{outer} {y} Q{x} {y - 8} {inner} {y}"
        out.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="9"/>')
    return "".join(out)


def mouth(c, shape):
    x, y = HX, MOUTH_Y
    if shape == "smile":
        return f'<path d="M{x - 30} {y - 4} Q{x} {y + 22} {x + 30} {y - 4}" fill="none" stroke-width="6"/>'
    if shape == "flat":
        return f'<path d="M{x - 22} {y + 4} L{x + 22} {y + 4}" fill="none" stroke-width="6"/>'
    if shape == "frown":
        return f'<path d="M{x - 28} {y + 12} Q{x} {y - 10} {x + 28} {y + 12}" fill="none" stroke-width="6"/>'
    if shape == "small":
        return (f'<ellipse cx="{x}" cy="{y + 4}" rx="20" ry="14" fill="#7a1f1f" stroke-width="5"/>'
                f'<ellipse cx="{x}" cy="{y + 12}" rx="11" ry="5" fill="#ff6b6b" stroke="none"/>')
    if shape == "big":
        return (f'<path d="M{x - 38} {y - 8} Q{x} {y - 2} {x + 38} {y - 8} Q{x + 30} {y + 45} {x} {y + 45} '
                f'Q{x - 30} {y + 45} {x - 38} {y - 8} Z" fill="#7a1f1f" stroke-width="5"/>'
                f'<path d="M{x - 30} {y - 4} Q{x} {y + 6} {x + 30} {y - 4} L{x + 26} {y + 6} Q{x} {y + 14} {x - 26} {y + 6} Z" '
                f'fill="#ffffff" stroke="none"/>'
                f'<ellipse cx="{x}" cy="{y + 34}" rx="18" ry="8" fill="#ff6b6b" stroke="none"/>')
    if shape == "o":
        return f'<ellipse cx="{x}" cy="{y + 8}" rx="16" ry="22" fill="#7a1f1f" stroke-width="5"/>'
    raise ValueError(shape)


def top(c):
    out = []
    if c.get("bindi"):
        out.append(f'<circle cx="{HX}" cy="{EYE_Y - 70}" r="8" fill="#d00000" stroke="none"/>')
    if c.get("moustache") == "thin":
        out.append(f'<path d="M{HX - 42} {MOUTH_Y - 8} Q{HX - 20} {MOUTH_Y - 30} {HX} {MOUTH_Y - 18} '
                   f'Q{HX + 20} {MOUTH_Y - 30} {HX + 42} {MOUTH_Y - 8} Q{HX} {MOUTH_Y - 14} {HX - 42} {MOUTH_Y - 8} Z" '
                   f'fill="#1b1b1b" stroke-width="3"/>')
    if c.get("moustache") == "big":
        out.append(f'<path d="M{HX - 70} {MOUTH_Y - 2} Q{HX - 50} {MOUTH_Y - 45} {HX} {MOUTH_Y - 24} '
                   f'Q{HX + 50} {MOUTH_Y - 45} {HX + 70} {MOUTH_Y - 2} Q{HX + 40} {MOUTH_Y - 18} {HX} {MOUTH_Y - 10} '
                   f'Q{HX - 40} {MOUTH_Y - 18} {HX - 70} {MOUTH_Y - 2} Z" fill="#2a2a2a" stroke-width="3"/>')
    if c.get("glasses") == "rect":
        for sx in (-1, 1):
            out.append(f'<rect x="{HX + sx * EYE_DX - 36}" y="{EYE_Y - 30}" width="72" height="58" rx="12" '
                       f'fill="#ffffff" fill-opacity="0.12" stroke-width="6"/>')
        out.append(f'<path d="M{HX - 16} {EYE_Y - 8} Q{HX} {EYE_Y - 18} {HX + 16} {EYE_Y - 8}" fill="none" stroke-width="6"/>')
    if c.get("glasses") == "round":
        for sx in (-1, 1):
            out.append(f'<circle cx="{HX + sx * EYE_DX}" cy="{EYE_Y}" r="38" fill="#ffffff" fill-opacity="0.12" '
                       f'stroke="#8d6e63" stroke-width="6"/>')
        out.append(f'<path d="M{HX - 14} {EYE_Y - 6} Q{HX} {EYE_Y - 14} {HX + 14} {EYE_Y - 6}" fill="none" '
                   f'stroke="#8d6e63" stroke-width="6"/>')
    return "".join(out)


def layers(c):
    L = {"base": base(c), "top": top(c)}
    for p in ("down", "up", "hips"):
        L[f"arms_{p}"] = arms(c, p)
    for e in ("open", "closed", "happy"):
        L[f"eyes_{e}"] = eyes(c, e)
    for e in ("neutral", "happy", "angry", "sad", "surprised"):
        L[f"brows_{e}"] = brows(c, e)
    for m in ("smile", "flat", "frown", "small", "big", "o"):
        L[f"mouth_{m}"] = mouth(c, m)
    return L


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        for name, c in CAST.items():
            d = OUT / name
            d.mkdir(exist_ok=True)
            for lname, body in layers(c).items():
                pg.set_content(f'<html><body style="margin:0;background:transparent">{svg(body)}</body></html>')
                pg.screenshot(path=str(d / f"{lname}.png"), omit_background=True,
                              clip={"x": 0, "y": 0, "width": W, "height": H})
            meta[name] = {"scale": c["scale"], "kind": c["kind"]}
        b.close()
    (OUT / "cast.json").write_text(json.dumps(meta, indent=1))
    print("done:", ", ".join(meta))


if __name__ == "__main__":
    main()
