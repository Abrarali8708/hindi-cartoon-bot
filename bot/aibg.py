"""Optional AI backgrounds from Cloudflare Workers AI (free daily allowance).
Falls back to the built-in drawn backgrounds if not configured or if anything fails."""
import base64
import io
import os
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
STYLE = ("flat 2D cartoon background illustration for a children's animated TV show, clean bold outlines, "
         "bright cheerful colours, simple shapes, Indian setting, empty scene with NO people and NO text, "
         "wide shot, eye level")
PLACE_PROMPTS = {
    "living_room": "cosy middle-class Indian living room with sofa, TV cabinet, window, potted plant",
    "kitchen": "Indian home kitchen with gas stove, pressure cooker, steel utensils on shelves, tiled wall",
    "classroom": "Indian school classroom with green chalkboard, wooden desks and benches",
    "park": "Indian neighbourhood park with trees, swings, bench, sunny sky",
    "market": "colourful Indian street market with fruit and vegetable stalls and shop awnings",
    "bedroom": "Indian kids bedroom at night with bed, study table, window with moon",
}


def builtin(place, tall):
    return Image.open(ROOT / "assets" / "backgrounds" / f"{place}_{'tall' if tall else 'wide'}.png").convert("RGB")


def background(place, size, use_ai, cache_dir):
    """Return an RGB background of exactly `size` (w, h)."""
    W, H = size
    tall = H > W
    img = None
    if use_ai and os.environ.get("CF_ACCOUNT_ID") and os.environ.get("CF_API_TOKEN"):
        try:
            img = _cloudflare(f"{PLACE_PROMPTS[place]}, {STYLE}")
            print(f"    AI background: {place}")
        except Exception as e:
            print(f"    (AI background failed, using built-in: {e})")
    if img is None:
        img = builtin(place, tall)
    return _cover(img, W, H)


def _cloudflare(prompt):
    acct, tok = os.environ["CF_ACCOUNT_ID"], os.environ["CF_API_TOKEN"]
    r = requests.post(f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/@cf/black-forest-labs/flux-1-schnell",
                      headers={"Authorization": f"Bearer {tok}"}, json={"prompt": prompt, "steps": 6}, timeout=90)
    r.raise_for_status()
    b64 = r.json()["result"]["image"]
    return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")


def _cover(img, W, H):
    """Scale and centre-crop so the image fills W x H."""
    s = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x, y = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((x, y, x + W, y + H))
