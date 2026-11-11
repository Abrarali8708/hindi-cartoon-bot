# Hindi family-comedy cartoon bot (free, fully automatic)

Every day it writes a brand-new funny Hindi story with a small moral, voices every character, animates the
cartoon family (blinking, talking, reacting), adds Hindi captions and sound effects, and uploads to YouTube.

| What | When (India time) |
|---|---|
| 2 Shorts (vertical, ~45 s) | 12:30 PM and 7:30 PM, every day |
| 4 long episodes (~6-8 min) | 6:00 PM on Sun, Mon, Wed, Fri |

Cast: Chintu, Pinky, Mummy, Papa, Dadi and Gupta ji (neighbour). All original characters.

**Cost: $0** — Gemini free tier (story), Cloudflare free tier (backgrounds), Microsoft Edge voices (free),
GitHub Actions (free and unlimited for public repositories).

---

## One-time setup (about 40 minutes)

### Step 1: Create the YouTube channel
1. In YouTube, click your picture → **Settings → Add or manage your channels → Create a channel**.
2. Name it, then verify it at **youtube.com/verify** (needed for custom thumbnails).

### Step 2: Free story-writing key (Gemini)
1. Open **aistudio.google.com** → **Get API key** → **Create API key**.
2. Copy it. This is `GEMINI_API_KEY`.

### Step 3: Free background-drawing key (Cloudflare) — optional
Without it the bot uses its own built-in drawn backgrounds.
1. Sign up free at **dash.cloudflare.com**.
2. Copy your **Account ID** (right side of the dashboard home, or in the URL). This is `CF_ACCOUNT_ID`.
3. Go to **My Profile → API Tokens → Create Token → "Workers AI" template → Create**. Copy it. This is `CF_API_TOKEN`.

### Step 4: Connect the new channel to YouTube uploads
You can reuse the same Google Cloud project and `client_secret.json` from your first bot.
1. Copy `client_secret.json` into this folder.
2. Run:
   ```
   pip install -r requirements.txt
   python get_refresh_token.py
   ```
3. In the browser, pick the **new channel** (not Anicq). Allow.
4. Keep the 3 printed values.

### Step 5: Put it on GitHub (public repo = unlimited free minutes)
1. Create a new **Public** repository, e.g. `hindi-cartoon-bot`. Secrets stay private even in a public repo.
2. Push this folder (`client_secret.json` is ignored automatically).
3. **Settings → Secrets and variables → Actions**, add:
   `GEMINI_API_KEY`, `CF_ACCOUNT_ID`, `CF_API_TOKEN`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`
4. **Settings → Actions → General → Workflow permissions → Read and write → Save**.

### Step 6: Test
1. In `config.yaml` set `privacy: "private"` and your channel name.
2. **Actions → Make and upload a cartoon Short → Run workflow**. Check it in YouTube Studio.
3. If it looks good, set `privacy: "public"` and push. Done.

---

## Settings (`config.yaml`)
| Setting | Meaning |
|---|---|
| `channel_name` | shown on the title and ending cards |
| `ai_backgrounds` | `false` = always use the built-in drawn backgrounds |
| `music_volume` | put royalty-free `.mp3` files from the YouTube Audio Library in `music/` |
| `made_for_kids` | `false` = family comedy for all ages. Set `true` only if you change to kids-only content |

Test on your PC without uploading: `python run.py short --no-upload` (needs `GEMINI_API_KEY` set).

## Safety built in
Every script is checked twice before it is made: a blocked-words list, then a second AI review that rejects
anything a parent wouldn't want a 6-year-old to hear. Rejected scripts are rewritten automatically.
