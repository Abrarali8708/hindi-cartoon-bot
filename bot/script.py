"""Write a new Hindi family-comedy episode with Google Gemini (free tier), then safety-check it."""
import json
import os
import random
import re
import time

import requests

CAST = {
    "chintu": "Chintu, 9-year-old naughty but good-hearted boy, always has a funny 'smart' plan that backfires",
    "pinky": "Pinky, Chintu's 6-year-old sister, innocent, says the honest truth at the worst moment",
    "mummy": "Mummy, sharp and loving homemaker, catches every lie, famous for her one-line comebacks",
    "papa": "Papa, office-going dad, lazy on Sundays, tries to act strict but is a softie, loves cricket and chai",
    "dadi": "Dadi, wise and witty grandmother, tells old-time stories, secretly sides with the kids",
    "guptaji": "Gupta ji, the nosy neighbour uncle, shows off constantly, always asks 'kitne number aaye?'",
}
PLACES = ["living_room", "kitchen", "classroom", "park", "market", "bedroom"]
EMOTIONS = ["neutral", "happy", "laugh", "angry", "sad", "surprised"]
SFX = ["", "boing", "whoosh", "pop", "ding", "punchline", "gasp"]

SEEDS = [
    "exam result day", "Chintu hides a bad report card", "power cut on a hot summer night", "guests arrive suddenly",
    "Diwali cleaning", "Sunday cricket match at home", "Papa's diet plan", "Mummy's new cooking experiment",
    "Pinky's first day at school", "lost TV remote", "Dadi learns to use a smartphone", "monsoon flooding the street",
    "school science project the night before", "Chintu wants a pet dog", "family wedding preparations",
    "mobile phone screen-time rules", "Gupta ji shows off his new car", "homework excuses", "the last samosa",
    "Papa tries to fix the fan himself", "summer vacation plans", "Raksha Bandhan gift", "school sports day",
    "Holi colours everywhere", "doctor's injection fear", "Chintu tries to cook Maggi alone", "piggy bank savings",
    "parent-teacher meeting", "Dadi's lost glasses (on her head)", "neighbour's mango tree", "online class chaos",
    "Papa's office video call at home", "early morning yoga plan", "kite flying on Makar Sankranti",
    "new year resolutions", "a surprise birthday party", "train journey to nani's house", "spelling bee",
    "Chintu becomes 'class monitor'", "saving water challenge", "planting a tree", "learning to ride a cycle",
    "Ganesh Chaturthi decorations", "a mysterious noise in the store room (it's the cat)", "Mummy on a no-sugar week",
    "bargaining at the vegetable market", "Pinky's tooth fairy", "cleaning up the park", "helping an elderly neighbour",
]

RULES = """
RULES (very important):
- Clean family comedy for ALL ages. Absolutely NO adult jokes, double meaning, romance, alcohol, smoking, gambling,
  horror, gore, real violence, hitting or punishing children, insults about body/skin/caste/religion/region/gender.
- Light slapstick is fine (slipping on a banana peel, a fan blowing papers). Nobody gets hurt.
- No real people, brands, films, songs, politicians or celebrities. Original story only.
- Simple everyday Hindi in Devanagari script (Hindustani, as Indian families speak; common English words like
  "school", "phone", "homework" are fine). Short lines, max 18 words each.
- Funny, warm, relatable. Each scene must have at least one clear joke or funny twist.
- End with a gentle moral (one short sentence) that the story actually shows, not preachy.
"""


def _prompt(kind, seed, recent):
    if kind == "short":
        size = ("ONE scene (two scenes max), 8 to 12 lines, about 90 to 120 Hindi words in total (about 45 seconds). "
                "First line must be a strong funny hook. Last story line must be the punchline.")
    else:
        size = ("5 to 7 scenes, 55 to 75 lines in total (about 7 minutes). A clear beginning, a growing problem, "
                "a big funny climax, and a warm ending.")
    cast = "\n".join(f"- {k}: {v}" for k, v in CAST.items())
    return f"""You write scripts for a Hindi animated family-comedy cartoon channel watched by kids and adults in India.

CHARACTERS (use only these ids; 2 or 3 characters per scene; "narrator" may speak briefly):
{cast}

STORY IDEA: {seed}
LENGTH: {size}
Do NOT repeat these recent episode titles: {", ".join(recent) or "none"}
{RULES}
Return ONLY JSON in exactly this shape:
{{
 "title": "catchy YouTube title in Hindi (Devanagari) + a few English words, max 70 characters, no clickbait lies",
 "thumb_text": "2 to 4 Hindi words for the thumbnail",
 "description": "2-3 sentence YouTube description in Hindi",
 "tags": ["8 short tags in Hindi or English"],
 "moral": "one short Hindi sentence",
 "scenes": [
  {{"place": one of {PLACES},
    "cast": ["2 or 3 character ids"],
    "lines": [{{"who": "character id from this scene's cast or narrator", "emotion": one of {EMOTIONS},
               "text": "Hindi line", "sfx": one of {SFX}}}]}}
 ]
}}"""


def _gemini(prompt, cfg, want_json=True):
    key = os.environ["GEMINI_API_KEY"]
    last = None
    for model in cfg.get("gemini_models", ["gemini-flash-lite-latest", "gemini-flash-latest"]):
        for attempt in range(3):
            try:
                r = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    params={"key": key}, timeout=120,
                    json={"contents": [{"parts": [{"text": prompt}]}],
                          "generationConfig": {"temperature": 1.0,
                                               **({"responseMimeType": "application/json"} if want_json else {})}})
                if r.status_code in (429, 500, 503):
                    last = f"{model}: {r.status_code}"
                    time.sleep(15 * (attempt + 1))
                    continue
                r.raise_for_status()
                txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(_strip(txt)) if want_json else txt
            except (requests.RequestException, KeyError, json.JSONDecodeError) as e:
                last = f"{model}: {e}"
                time.sleep(5)
    raise RuntimeError(f"Gemini failed: {last}")


def _strip(t):
    t = t.strip()
    t = re.sub(r"^```(json)?", "", t).strip()
    return re.sub(r"```$", "", t).strip()


BLOCK = ["sexy", "kiss", "daaru", "दारू", "शराब", "sharab", "cigarette", "सिगरेट", "बीड़ी", "जुआ", "गाली", "maar dunga",
         "मार दूंगा", "मार डालूंगा", "खून", "काला है", "मोटी", "मोटा", "चुड़ैल", "प्यार हो गया",
         "girlfriend", "boyfriend", "गर्लफ्रेंड", "बॉयफ्रेंड", "थप्पड़", "चप्पल से"]


def validate(s, kind):
    """Fix small issues, reject bad scripts. Returns cleaned script."""
    scenes = []
    for sc in s.get("scenes", []):
        place = sc.get("place") if sc.get("place") in PLACES else random.choice(PLACES)
        cast = [c for c in sc.get("cast", []) if c in CAST][:3]
        lines = []
        for ln in sc.get("lines", []):
            who = ln.get("who")
            text = str(ln.get("text", "")).strip()
            if not text or (who not in CAST and who != "narrator"):
                continue
            if who in CAST and who not in cast:
                if len(cast) >= 3:
                    continue
                cast.append(who)
            lines.append({"who": who, "text": text[:220],
                          "emotion": ln.get("emotion") if ln.get("emotion") in EMOTIONS else "neutral",
                          "sfx": ln.get("sfx") if ln.get("sfx") in SFX else ""})
        if lines and cast:
            scenes.append({"place": place, "cast": cast, "lines": lines})
    n = sum(len(sc["lines"]) for sc in scenes)
    lo, hi = (6, 16) if kind == "short" else (38, 95)
    if not (lo <= n <= hi):
        raise ValueError(f"script has {n} lines, expected {lo}-{hi}")
    whole = json.dumps(s, ensure_ascii=False).lower()
    bad = [w for w in BLOCK if w.lower() in whole]
    if bad:
        raise ValueError(f"blocked words: {bad}")
    for k in ("title", "moral"):
        if not str(s.get(k, "")).strip():
            raise ValueError(f"missing {k}")
    s["scenes"] = scenes
    s["tags"] = [str(t)[:30] for t in s.get("tags", [])][:12]
    s["thumb_text"] = str(s.get("thumb_text") or s["title"])[:40]
    return s


def safety_review(s, cfg):
    prompt = ("You are a strict content reviewer for a family cartoon channel watched by children in India. "
              "Check this script for ANY adult/double-meaning humour, romance, violence against anyone, "
              "hitting/punishing kids, scary content, insults about body/caste/religion/region/gender, real brands "
              "or people, or anything a parent would not want a 6-year-old to hear. Return JSON "
              '{"safe": true/false, "reason": "short reason"}.\n\nSCRIPT:\n' + json.dumps(s, ensure_ascii=False))
    r = _gemini(prompt, cfg)
    return bool(r.get("safe")), str(r.get("reason", ""))


def write_episode(kind, cfg, recent_titles):
    last = None
    for attempt in range(4):
        seed = random.choice(SEEDS)
        try:
            s = validate(_gemini(_prompt(kind, seed, recent_titles[-30:]), cfg), kind)
            ok, why = safety_review(s, cfg)
            if not ok:
                raise ValueError(f"safety review rejected: {why}")
            s["seed"] = seed
            return s
        except Exception as e:
            last = e
            print(f"  script attempt {attempt + 1} failed: {e}")
            time.sleep(5)
    raise RuntimeError(f"Could not write a good script: {last}")
