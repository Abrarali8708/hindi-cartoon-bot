"""Draw built-in cartoon backgrounds (used when AI backgrounds are off or unavailable).
Each scene is drawn twice: 1920x1080 (long videos) and 1080x1920 (Shorts)."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "assets/backgrounds")
INK = "#2b1d14"


def frame(W, H, inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7dd3fc"/>'
            f'<stop offset="1" stop-color="#e0f2fe"/></linearGradient>'
            f'<linearGradient id="night" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1e1b4b"/>'
            f'<stop offset="1" stop-color="#4338ca"/></linearGradient></defs>'
            f'<g stroke="{INK}" stroke-width="6" stroke-linejoin="round" stroke-linecap="round">{inner}</g></svg>')


def window(x, y, w, h, night=False):
    sky = "url(#night)" if night else "url(#sky)"
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{sky}"/>'
    if night:
        s += f'<circle cx="{x + w * 0.7}" cy="{y + h * 0.3}" r="{min(w, h) * 0.12}" fill="#fef9c3" stroke="none"/>'
    else:
        s += f'<ellipse cx="{x + w * 0.3}" cy="{y + h * 0.35}" rx="{w * 0.15}" ry="{h * 0.07}" fill="#fff" stroke="none"/>'
    s += (f'<line x1="{x + w / 2}" y1="{y}" x2="{x + w / 2}" y2="{y + h}"/><line x1="{x}" y1="{y + h / 2}" '
          f'x2="{x + w}" y2="{y + h / 2}"/>')
    s += (f'<path d="M{x - 30} {y - 20} Q{x + 20} {y + h * 0.5} {x - 10} {y + h + 20} L{x - 40} {y + h + 20} L{x - 40} '
          f'{y - 20} Z" fill="#f4a261"/><path d="M{x + w + 30} {y - 20} Q{x + w - 20} {y + h * 0.5} {x + w + 10} '
          f'{y + h + 20} L{x + w + 40} {y + h + 20} L{x + w + 40} {y - 20} Z" fill="#f4a261"/>')
    return s


def living(W, H):
    fl = H * 0.68
    s = f'<rect x="-5" y="-5" width="{W + 10}" height="{fl + 5}" fill="#fde2b8" stroke="none"/>'
    s += f'<rect x="-5" y="{fl}" width="{W + 10}" height="{H - fl + 5}" fill="#c08457"/>'
    s += "".join(f'<line x1="{x}" y1="{fl}" x2="{x - 120}" y2="{H}" stroke-width="3" opacity="0.4"/>'
                 for x in range(0, int(W) + 200, 160))
    s += window(W * 0.08, H * 0.12, W * 0.22, H * 0.3)
    s += f'<rect x="{W * 0.42}" y="{H * 0.14}" width="{W * 0.16}" height="{H * 0.18}" rx="6" fill="#ffd166"/>'
    s += f'<circle cx="{W * 0.5}" cy="{H * 0.23}" r="{H * 0.05}" fill="#f77f00"/>'
    # sofa
    sx, sy, sw = W * 0.62, fl - H * 0.2, W * 0.32
    s += f'<rect x="{sx}" y="{sy}" width="{sw}" height="{H * 0.16}" rx="30" fill="#e76f51"/>'
    s += f'<rect x="{sx - 25}" y="{sy + H * 0.05}" width="{sw + 50}" height="{H * 0.17}" rx="25" fill="#f4a261"/>'
    # plant + lamp
    s += f'<rect x="{W * 0.36}" y="{fl - H * 0.1}" width="{W * 0.05}" height="{H * 0.1}" rx="8" fill="#9c6644"/>'
    s += "".join(f'<ellipse cx="{W * 0.385 + dx}" cy="{fl - H * 0.15 + dy}" rx="{W * 0.018}" ry="{H * 0.05}" '
                 f'fill="#52b788" transform="rotate({r} {W * 0.385 + dx} {fl - H * 0.15 + dy})"/>'
                 for dx, dy, r in ((-25, 0, -25), (25, 0, 25), (0, -25, 0)))
    return s


def kitchen(W, H):
    fl = H * 0.7
    s = f'<rect x="-5" y="-5" width="{W + 10}" height="{fl + 5}" fill="#d8f3dc" stroke="none"/>'
    for y in range(int(H * 0.3), int(fl), 60):
        for x in range(0, int(W), 60):
            s += f'<rect x="{x}" y="{y}" width="60" height="60" fill="none" stroke="#95d5b2" stroke-width="2"/>'
    s += f'<rect x="-5" y="{fl}" width="{W + 10}" height="{H - fl + 5}" fill="#adb5bd"/>'
    cy = fl - H * 0.17
    s += f'<rect x="{W * 0.05}" y="{cy}" width="{W * 0.9}" height="{H * 0.05}" fill="#6c757d"/>'
    s += f'<rect x="{W * 0.05}" y="{cy + H * 0.05}" width="{W * 0.9}" height="{H * 0.12}" fill="#8d6e63"/>'
    for i in range(5):
        x = W * 0.05 + i * W * 0.18
        s += f'<rect x="{x + 10}" y="{cy + H * 0.06}" width="{W * 0.16}" height="{H * 0.1}" rx="6" fill="#a1887f"/>'
    # stove + cooker
    s += f'<rect x="{W * 0.15}" y="{cy - H * 0.03}" width="{W * 0.2}" height="{H * 0.03}" rx="6" fill="#343a40"/>'
    s += (f'<rect x="{W * 0.19}" y="{cy - H * 0.13}" width="{W * 0.08}" height="{H * 0.1}" rx="16" fill="#ced4da"/>'
          f'<rect x="{W * 0.215}" y="{cy - H * 0.16}" width="{W * 0.03}" height="{H * 0.03}" rx="5" fill="#212529"/>')
    # shelf with jars
    s += f'<rect x="{W * 0.55}" y="{H * 0.17}" width="{W * 0.36}" height="{H * 0.02}" fill="#8d6e63"/>'
    for i, col in enumerate(("#ffb703", "#e63946", "#2a9d8f", "#f4a261")):
        s += f'<rect x="{W * 0.57 + i * W * 0.085}" y="{H * 0.09}" width="{W * 0.06}" height="{H * 0.08}" rx="10" fill="{col}"/>'
    s += window(W * 0.2, H * 0.08, W * 0.18, H * 0.18)
    return s


def classroom(W, H):
    fl = H * 0.72
    s = f'<rect x="-5" y="-5" width="{W + 10}" height="{fl + 5}" fill="#fff1c1" stroke="none"/>'
    s += f'<rect x="-5" y="{fl}" width="{W + 10}" height="{H - fl + 5}" fill="#b08968"/>'
    s += f'<rect x="{W * 0.18}" y="{H * 0.1}" width="{W * 0.64}" height="{H * 0.33}" rx="10" fill="#2d6a4f"/>'
    s += f'<rect x="{W * 0.18}" y="{H * 0.43}" width="{W * 0.64}" height="{H * 0.02}" fill="#8d6e63"/>'
    s += (f'<text x="{W * 0.5}" y="{H * 0.3}" font-family="Poppins, sans-serif" font-size="{H * 0.09}" fill="#ffffff" '
          f'stroke="none" text-anchor="middle" opacity="0.85">2 + 2 = ?</text>')
    s += f'<circle cx="{W * 0.9}" cy="{H * 0.16}" r="{H * 0.05}" fill="#ffffff"/>'
    s += f'<path d="M{W * 0.9} {H * 0.16} l0 -{H * 0.03} M{W * 0.9} {H * 0.16} l{H * 0.02} 0" stroke-width="5"/>'
    for i in range(3):
        x = W * (0.08 + i * 0.32)
        s += f'<rect x="{x}" y="{fl - H * 0.08}" width="{W * 0.22}" height="{H * 0.04}" rx="6" fill="#ddb892"/>'
        s += f'<rect x="{x + 15}" y="{fl - H * 0.04}" width="12" height="{H * 0.1}" fill="#7f5539"/>'
        s += f'<rect x="{x + W * 0.22 - 27}" y="{fl - H * 0.04}" width="12" height="{H * 0.1}" fill="#7f5539"/>'
    return s


def park(W, H):
    gl = H * 0.66
    s = f'<rect x="-5" y="-5" width="{W + 10}" height="{gl + 5}" fill="url(#sky)" stroke="none"/>'
    s += f'<circle cx="{W * 0.85}" cy="{H * 0.13}" r="{H * 0.07}" fill="#ffd166"/>'
    for cx, cy in ((0.2, 0.12), (0.5, 0.2)):
        s += "".join(f'<circle cx="{W * cx + dx}" cy="{H * cy}" r="{H * 0.04}" fill="#fff" stroke="none"/>'
                     for dx in (-50, 0, 50))
    s += f'<path d="M-5 {gl} Q{W * 0.3} {gl - H * 0.06} {W * 0.6} {gl} T{W + 5} {gl} L{W + 5} {H + 5} L-5 {H + 5} Z" fill="#74c69d"/>'
    for tx in (0.1, 0.78):
        x = W * tx
        s += f'<rect x="{x - W * 0.015}" y="{gl - H * 0.2}" width="{W * 0.03}" height="{H * 0.22}" fill="#7f5539"/>'
        s += f'<circle cx="{x}" cy="{gl - H * 0.27}" r="{H * 0.12}" fill="#40916c"/>'
    bx = W * 0.4
    s += f'<rect x="{bx}" y="{gl - H * 0.06}" width="{W * 0.2}" height="{H * 0.03}" rx="6" fill="#bc6c25"/>'
    s += f'<rect x="{bx}" y="{gl - H * 0.11}" width="{W * 0.2}" height="{H * 0.03}" rx="6" fill="#dda15e"/>'
    return s


def market(W, H):
    gl = H * 0.7
    s = f'<rect x="-5" y="-5" width="{W + 10}" height="{gl + 5}" fill="url(#sky)" stroke="none"/>'
    cols = ["#e63946", "#2a9d8f", "#f4a261", "#8338ec", "#ffb703"]
    n = 4 if W > H else 2
    sw = W / n
    for i in range(n):
        x = i * sw
        s += f'<rect x="{x + 10}" y="{H * 0.18}" width="{sw - 20}" height="{gl - H * 0.18}" fill="#fefae0"/>'
        s += f'<rect x="{x + 10}" y="{H * 0.18}" width="{sw - 20}" height="{H * 0.08}" fill="{cols[i % 5]}"/>'
        stripes = "".join(f'<path d="M{x + 10 + k * (sw - 20) / 6} {H * 0.26} q{(sw - 20) / 12} {H * 0.04} '
                          f'{(sw - 20) / 6} 0" fill="{cols[(i + 1) % 5]}"/>' for k in range(6))
        s += stripes
        s += f'<rect x="{x + 30}" y="{H * 0.35}" width="{sw - 60}" height="{gl - H * 0.45}" fill="#ffe8d6"/>'
        for k in range(4):
            s += f'<circle cx="{x + 60 + k * (sw - 120) / 3}" cy="{gl - H * 0.13}" r="{H * 0.025}" fill="{cols[(i + k) % 5]}"/>'
    s += f'<rect x="-5" y="{gl}" width="{W + 10}" height="{H - gl + 5}" fill="#b7b7a4"/>'
    return s


def bedroom(W, H):
    fl = H * 0.68
    s = f'<rect x="-5" y="-5" width="{W + 10}" height="{fl + 5}" fill="#cdb4db" stroke="none"/>'
    s += f'<rect x="-5" y="{fl}" width="{W + 10}" height="{H - fl + 5}" fill="#9d8189"/>'
    s += window(W * 0.62, H * 0.1, W * 0.22, H * 0.28, night=True)
    bx, by = W * 0.05, fl - H * 0.15
    s += f'<rect x="{bx}" y="{by - H * 0.12}" width="{W * 0.05}" height="{H * 0.27}" rx="10" fill="#6d597a"/>'
    s += f'<rect x="{bx}" y="{by}" width="{W * 0.42}" height="{H * 0.13}" rx="14" fill="#b56576"/>'
    s += f'<rect x="{bx + W * 0.06}" y="{by - H * 0.05}" width="{W * 0.1}" height="{H * 0.06}" rx="20" fill="#ffffff"/>'
    s += f'<rect x="{bx + W * 0.18}" y="{by - H * 0.03}" width="{W * 0.24}" height="{H * 0.06}" rx="14" fill="#e56b6f"/>'
    return s


SCENES = {"living_room": living, "kitchen": kitchen, "classroom": classroom, "park": park, "market": market,
          "bedroom": bedroom}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        for (W, H), tag in (((1920, 1080), "wide"), ((1080, 1920), "tall")):
            pg = b.new_page(viewport={"width": W, "height": H})
            for name, fn in SCENES.items():
                pg.set_content(f'<html><body style="margin:0">{frame(W, H, fn(W, H))}</body></html>')
                pg.screenshot(path=str(OUT / f"{name}_{tag}.png"))
        b.close()
    print("backgrounds:", ", ".join(SCENES))


if __name__ == "__main__":
    main()
